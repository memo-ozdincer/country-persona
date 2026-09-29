"""Run one bounded, traced Qwen3 inference pack; preflight is safe without a GPU."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

from country_persona.inference_probe import generation_config, run_cases, tokenize_cases, verify_snapshot
from country_persona.io import read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=Path("configs/posttraining/model.lock.json"))
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--model-receipt", type=Path, default=Path("reports/trillium_model_verification.json"))
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--eos-policy", choices=("model", "legacy-tokenizer"), default="model")
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--context-budget", type=int, default=8192)
    parser.add_argument("--case-cap", type=int, default=8)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output directory")
    lock = json.loads(args.lock.read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Local tokenizer/config differs from the lock")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    if manifest["files_sha256"]["cases.jsonl"] != sha256(args.pack / "cases.jsonl"):
        raise ValueError("Case file differs from the frozen pack")
    if "planned_model_lock_sha256" in manifest and manifest["planned_model_lock_sha256"] != sha256(args.lock):
        raise ValueError("Selected probe was prepared against a different model lock")
    cases = list(read_jsonl(args.pack / "cases.jsonl"))
    from transformers import AutoTokenizer, GenerationConfig
    import transformers

    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True, trust_remote_code=False)
    source_generation = GenerationConfig.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    config, model_eos = generation_config(source_generation, tokenizer, args.max_new_tokens, args.eos_policy)
    tokenized, label_ids = tokenize_cases(cases, tokenizer, lock["chat_template_kwargs"], args.context_budget,
                                        args.max_new_tokens, args.case_cap)
    preflight = {"status": "tokenizer_only_no_model_inference", "cases": len(cases),
                 "case_file_sha256": sha256(args.pack / "cases.jsonl"),
                 "pack_manifest_sha256": sha256(args.pack / "manifest.json"), "model_lock_sha256": sha256(args.lock),
                 "model": lock["model"], "revision": lock["revision"], "chat_template_kwargs": lock["chat_template_kwargs"],
                 "input_tokens": sum(len(r["input_ids"]) for r in tokenized),
                 "maximum_input_tokens": max(len(r["input_ids"]) for r in tokenized),
                 "input_token_digests": {r["case"]["id"]: r["input_ids_digest"] for r in tokenized},
                 "label_token_ids": label_ids, "context_budget": args.context_budget,
                 "eos_policy": args.eos_policy, "model_eos_ids": model_eos,
                 "generation_config": config.to_dict(), "generation_call_kwargs": {"use_model_defaults": False},
                 "weight_verification": "not_performed_in_preflight"}
    if args.preflight_only:
        args.output.mkdir(parents=True)
        write_json(args.output / "preflight.json", preflight)
        print(json.dumps({k: preflight[k] for k in ("status", "cases", "input_tokens", "maximum_input_tokens", "eos_policy", "model_eos_ids")}, indent=2))
        return
    import torch
    from transformers import AutoModelForCausalLM

    if not args.model_path:
        raise ValueError("Production inference requires an explicit verified local --model-path")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("The pinned production recipe requires a BF16-capable CUDA device")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("No CUDA device is visible")
    torch.cuda.set_device(0)
    torch.manual_seed(0)
    verification_start = time.perf_counter()
    receipt = json.loads(args.model_receipt.read_text())
    verified = verify_snapshot(args.model_path, lock, receipt)
    verification_seconds = time.perf_counter() - verification_start
    model_start = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False,
                                                torch_dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0")
    if model.config.model_type != "qwen3":
        raise ValueError("This bounded production recipe was checked for Qwen3")
    if args.context_budget > model.config.max_position_embeddings:
        raise ValueError("Requested budget exceeds the checkpoint context limit")
    adapter_meta = None
    if args.adapter:
        from peft import PeftModel
        provenance = args.adapter / "run.json"
        if not provenance.exists() and args.adapter.name.startswith("checkpoint-"):
            state = json.loads((args.adapter / "trainer_state.json").read_text())
            if str(state["global_step"]) != args.adapter.name.removeprefix("checkpoint-"):
                raise ValueError("Checkpoint step/provenance mismatch")
            provenance = args.adapter.parent / "run.json"
        trained = json.loads(provenance.read_text())
        if trained["arguments"]["revision"] != lock["revision"] or trained["chat_template_kwargs"] != lock["chat_template_kwargs"]:
            raise ValueError("Adapter model/template provenance differs from the evaluation lock")
        tensors = sorted(args.adapter.glob("*.safetensors"))
        if not tensors:
            raise ValueError("Expected an adapter saved as safetensors")
        adapter_meta = {"path": str(args.adapter), "run_sha256": sha256(provenance),
                        "files_sha256": {p.name: sha256(p) for p in [args.adapter / "adapter_config.json", *tensors]}}
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False, local_files_only=True)
    torch.cuda.synchronize()
    load_seconds = time.perf_counter() - model_start
    torch.cuda.reset_peak_memory_stats()
    metadata = {"run_kind": "pinned_model_development_inference", "preflight": preflight,
                "snapshot_verification": verified, "model_receipt_sha256": sha256(args.model_receipt),
                "adapter": adapter_meta, "seed": 0, "device": torch.cuda.get_device_name(0),
                "torch_version": torch.__version__, "transformers_version": transformers.__version__,
                "model_verification_seconds": verification_seconds, "model_load_seconds": load_seconds,
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                "source_code_sha256": {str(p): sha256(p) for p in [Path(__file__), Path("src/country_persona/inference_probe.py"),
                                                                  Path("src/country_persona/action_eval.py"), Path("src/country_persona/io.py")]}}
    result = run_cases(model, tokenizer, tokenized, config, model_eos, label_ids, args.output, metadata)
    result["peak_allocated_gpu_gib"] = torch.cuda.max_memory_allocated() / 2**30
    write_json(args.output / "run.json", result)
    print(json.dumps({k: result[k] for k in ("status", "completed_cases", "prompt_tokens", "generated_tokens", "generation_seconds", "peak_allocated_gpu_gib")}, indent=2))


if __name__ == "__main__":
    main()
