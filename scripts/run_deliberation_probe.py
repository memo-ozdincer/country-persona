"""Run a bounded, traced policy deliberation comparison, or tokenizer-only preflight."""
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import time

from country_persona.deliberation import CONDITIONS, PROTOCOL, run_condition
from country_persona.inference_probe import generation_config, infer_one, tokenize_cases, verify_snapshot
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/deliberation-probe-20260928-v1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh run directory")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    if manifest["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("Protocol changed since the pack was frozen")
    for name in ("scenarios.jsonl", "protocol.json"):
        if sha256(args.pack / name) != manifest["files_sha256"][name]:
            raise ValueError("Frozen inference inputs changed")
    scenarios = list(read_jsonl(args.pack / "scenarios.jsonl"))
    if len(scenarios) != 2:
        raise ValueError("This first bounded probe requires exactly two scenarios")
    lock_path = Path("configs/posttraining/model.lock.json")
    lock = json.loads(lock_path.read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Tokenizer/config lock mismatch")
    from transformers import AutoTokenizer, GenerationConfig
    import transformers
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True, trust_remote_code=False)
    source_config = GenerationConfig.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    metadata = {"status": "preflight_only" if args.preflight_only else "running", "started_at": datetime.now(timezone.utc).isoformat(),
                "model": lock["model"], "revision": lock["revision"], "chat_template_kwargs": lock["chat_template_kwargs"],
                "pack_manifest_sha256": sha256(args.pack / "manifest.json"), "protocol_sha256": digest(PROTOCOL),
                "model_lock_sha256": sha256(lock_path), "adapter": None, "completed_calls": 0,
                "source_code_sha256": {p: sha256(p) for p in [__file__, "src/country_persona/deliberation.py", "src/country_persona/inference_probe.py", "src/country_persona/action_eval.py"]}}
    model = None
    if not args.preflight_only:
        if not args.model_path:
            raise ValueError("Production inference requires an explicit local model path")
        import torch
        from transformers import AutoModelForCausalLM
        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("Expected a BF16-capable CUDA device")
        torch.cuda.set_device(0); torch.manual_seed(0)
        metadata["snapshot_verification"] = verify_snapshot(args.model_path, lock, json.loads(Path("reports/trillium_model_verification.json").read_text()))
        model = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False,
                                                    torch_dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0")
        if args.adapter:
            from peft import PeftModel
            trained = json.loads((args.adapter / "run.json").read_text())
            if trained["arguments"]["revision"] != lock["revision"] or trained["chat_template_kwargs"] != lock["chat_template_kwargs"]:
                raise ValueError("Adapter uses different base/template")
            tensors = list(args.adapter.glob("*.safetensors"))
            if not tensors:
                raise ValueError("Missing adapter weights")
            metadata["adapter"] = {"path": str(args.adapter), "files_sha256": {p.name: sha256(p) for p in [args.adapter / "adapter_config.json", args.adapter / "run.json", *tensors]}}
            model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False, local_files_only=True)
        model.eval()
        torch.cuda.reset_peak_memory_stats()
        metadata.update(device=torch.cuda.get_device_name(0), torch_version=torch.__version__, transformers_version=transformers.__version__,
                        slurm_job_id=os.environ.get("SLURM_JOB_ID"), seed=0, generation_call_kwargs={"use_model_defaults": False})
    args.output.mkdir(parents=True)
    write_json(args.output / "run.json", metadata)
    all_rows, plans = [], []

    def generate(case, cap, use_adapter):
        entries, ids = tokenize_cases([case], tokenizer, lock["chat_template_kwargs"], PROTOCOL["context_budget"], cap, 1)
        entry = entries[0]
        if args.preflight_only:
            # Illustrative length placeholders exercise dependencies and tokenizer
            # boundaries. Actual generations remain subject to runtime hard caps.
            return {"id": case["id"], "case_sha256": case["case_sha256"], "response_id": digest([case["id"], "placeholder"])[:24],
                    "output": "Placeholder " * (cap // 2), "prompt_tokens": len(entry["input_ids"]), "generated_tokens": cap,
                    "generation_seconds": 0.0, "generator_kind": "tokenizer_placeholder_not_model_output"}
        config, model_eos = generation_config(source_config, tokenizer, cap, "model")
        # The final aggregator stays fixed when comparing trained country agents.
        context = model.disable_adapter() if args.adapter and not use_adapter else nullcontext()
        with context:
            row = infer_one(model, tokenizer, entry, config, model_eos, ids)
        row["generator_kind"] = "pinned_qwen3_development_inference"
        row["generation_config"] = config.to_dict()
        row["adapter_active"] = bool(args.adapter and use_adapter)
        return row

    def record(row):
        all_rows.append(row)
        if not args.preflight_only:
            write_jsonl(args.output / "transcript.jsonl", all_rows)
            metadata["completed_calls"] = len(all_rows)
            write_json(args.output / "run.json", metadata)
    started = time.perf_counter()
    try:
        for scenario in scenarios:
            for condition in CONDITIONS:
                rows = run_condition(scenario, condition, generate, record)
                plans.append({"scenario_id": scenario["id"], "condition": condition, "calls": len(rows),
                              "prompt_tokens": sum(r["prompt_tokens"] for r in rows),
                              "generated_tokens": sum(r["generated_tokens"] for r in rows),
                              "generation_seconds": sum(r["generation_seconds"] for r in rows),
                              "maximum_prompt_tokens": max(r["prompt_tokens"] for r in rows),
                              "output_caps": None if args.preflight_only else sum(r["hit_output_cap"] for r in rows),
                              "quality_scores": None, "independent_ratings": 0})
        metadata.update(status="tokenizer_preflight_completed" if args.preflight_only else "completed",
                        completed_calls=len(all_rows), conditions=plans, elapsed_seconds=time.perf_counter() - started,
                        finished_at=datetime.now(timezone.utc).isoformat(), equal_actual_compute_claimed=False)
        if args.preflight_only:
            metadata["limits"] = ["No model was loaded; placeholder lengths are illustrative, not worst-case proofs or semantic outputs.",
                                  "Every actual prompt is rechecked without truncation before generation."]
        else:
            metadata["transcript_sha256"] = sha256(args.output / "transcript.jsonl")
            metadata["peak_allocated_gpu_gib"] = torch.cuda.max_memory_allocated() / 2 ** 30
    except Exception as error:
        metadata.update(status="failed", completed_calls=len(all_rows), error=str(error))
        raise
    finally:
        write_json(args.output / "run.json", metadata)
    print(json.dumps({k: metadata[k] for k in ("status", "completed_calls", "conditions")}, indent=2))


if __name__ == "__main__":
    main()
