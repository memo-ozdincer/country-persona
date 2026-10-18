"""Frozen four-example fit, then explicit stdin-driven evaluation on the same GPU.

Retains verified base weights during short manual inspections to avoid repeated
MFS model loads. No evaluation is queued: each command is sent only after the
previous artifact is inspected. Exits after five minutes without a command.
"""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.scenario_sft import load_pack, locked_runtime, train_loop, evaluate
from run_scenario_sft import fresh_adapter
from run_aurora_qwen35_smoke import identity, current_gpu, verify_model
from review_scenario_sft import validate_review

RELEASE = ROOT / "research/scenario-role-sft-20261017-v1"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--base-run", type=Path, required=True)
    p.add_argument("--gpu-uuid", required=True)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    launch = dict(identity=identity(), mode="fit", status="started", runtime=locked_runtime(),
        output=str(out), resident=True, code_sha256=sha256(Path(__file__)),
        production_model_calls=0, production_optimizer_updates=0)
    write_json(out / "launch.json", launch)
    try:
        cfg_path = RELEASE / "fit-config.json"
        config = json.loads(cfg_path.read_text())
        for key in ("code_sha256", "artifact_sha256"):
            for name, expected in config[key].items():
                if sha256(ROOT / name) != expected:
                    raise ValueError("Frozen parent changed: " + name)
        if config["release_sha256"] != sha256(RELEASE / "pack/release.json") or config["quality_review_sha256"] != sha256(RELEASE / "quality-review.json"):
            raise ValueError("Data/review release changed")
        expected = dict(rank=8, alpha=16, target_modules="all-linear", presentations=32, updates=128,
            seed=42, learning_rate=5e-5, weight_decay=0.0, clip_norm=1.0, batch_size=1, accumulation=1,
            max_length=8192, generation_max_new_tokens=2048)
        if config["training"] != expected:
            raise ValueError("This resident runner implements the frozen method only")
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        fitting, held = load_pack(ROOT, RELEASE / "pack", tok)
        inspection = json.loads((a.base_run / "inspection.json").read_text())
        prior = json.loads((a.base_run / "launch.json").read_text())
        responses = list(read_jsonl(a.base_run / "responses.jsonl"))
        if (prior.get("status"), prior.get("arm"), prior.get("format"), prior.get("fit_config_sha256")) != ("completed", "base", "sequence", sha256(cfg_path)):
            raise ValueError("Base is not the completed matched raw sequence control")
        if {r["id"] for r in responses} != {r["id"] for r in held} or inspection["decision"] != "run_four_example_fit":
            raise ValueError("Both base answers must be inspected before deciding to fit")
        if inspection["rubric_sha256"] != sha256(RELEASE / "rubric.json"):
            raise ValueError("Rubric changed")
        validate_review(inspection, responses, json.loads((RELEASE / "rubric.json").read_text()), sha256(a.base_run / "responses.jsonl"))
        launch.update(fit_config_sha256=sha256(cfg_path), base_inspection_sha256=sha256(a.base_run / "inspection.json"))
        launch["gpu"] = current_gpu(a.gpu_uuid)
        if launch["gpu"]["name"] != "NVIDIA RTX PRO 6000 Blackwell Server Edition":
            raise ValueError("Different comparison hardware")
        os.environ["CUDA_VISIBLE_DEVICES"] = a.gpu_uuid
        launch["model_verification"] = verify_model(config)
        current_gpu(a.gpu_uuid)
        write_json(out / "launch.json", launch)
        import torch
        from transformers import Qwen3_5ForCausalLM
        from country_persona.training_checks import adapter_snapshot, tensor_state_digest
        torch.manual_seed(42)
        model = Qwen3_5ForCausalLM.from_pretrained(config["model_path"], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0")
        model = fresh_adapter(model)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        result = train_loop(model, fitting, presentations=32, seed=42, learning_rate=5e-5, output=out, device="cuda:0")
        launch.update(status="completed", production_optimizer_updates=result["steps"], result=result,
                      process_state="awaiting_explicit_operation")
        write_json(out / "launch.json", launch)
        state = tensor_state_digest(adapter_snapshot(model))
        evaluations = []
        while True:
            print(json.dumps({"state": "awaiting_explicit_operation", "idle_timeout_seconds": 300}), flush=True)
            if not select.select([sys.stdin], [], [], 300)[0]:
                break
            line = sys.stdin.readline()
            if not line:
                break
            command = json.loads(line)
            if command.get("operation") == "exit":
                break
            if command.get("operation") != "evaluate" or command.get("split") not in {"train", "eval"}:
                raise ValueError("Only explicit train/eval inspection or exit is supported")
            processes = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True)
            pids = {int(x.split(",")[1]) for x in processes.splitlines() if x.split(",")[0].strip() == a.gpu_uuid}
            if pids != {os.getpid()}:
                raise ValueError("GPU ownership changed; do not run another stage alongside unfamiliar processes")
            stage = Path(command["output"]).resolve()
            stage.mkdir(parents=True, exist_ok=False)
            if tensor_state_digest(adapter_snapshot(model)) != state:
                raise ValueError("Adapter state changed between explicit operations")
            info = dict(identity=identity(), mode="evaluate", arm="adapter", format="sequence",
                split=command["split"], status="started", resident_parent=str(out), gpu=launch["gpu"],
                fit_config_sha256=sha256(cfg_path), training_result_sha256=sha256(out / "training-result.json"),
                evaluation_code_sha256=sha256(ROOT / "src/country_persona/scenario_sft.py"),
                production_model_calls=0, production_optimizer_updates=0,
                serialization_scope="Same verified base and saved-adapter state, perturbed/reloaded in training checks; no separate cold 4B base reload.")
            write_json(stage / "launch.json", info)
            try:
                measured = evaluate(model, tok, fitting if command["split"] == "train" else held, stage, "cuda:0")
                if tensor_state_digest(adapter_snapshot(model)) != state:
                    raise ValueError("Evaluation mutated the adapter")
                info.update(status="completed", production_model_calls=measured["calls"], result=measured,
                            adapter_digest_unchanged=True)
                write_json(stage / "evaluation-result.json", measured)
                write_json(stage / "launch.json", info)
                evaluations.append(str(stage))
                print(json.dumps({"state": "evaluation_completed", "output": str(stage), "calls": measured["calls"]}), flush=True)
            except Exception as exc:
                r = stage / "responses.jsonl"
                info.update(status="failed", exception=repr(exc), traceback=traceback.format_exc(),
                    production_model_calls=len(r.read_text().splitlines()) if r.exists() else 0)
                write_json(stage / "launch.json", info)
                raise
        launch.update(process_state="exiting_normally", explicit_evaluations=evaluations)
        write_json(out / "launch.json", launch)
    except Exception as exc:
        if launch.get("status") != "completed":
            trace = out / "optimization.jsonl"
            launch.update(status="failed", production_optimizer_updates=len(trace.read_text().splitlines()) if trace.exists() else 0)
        launch.update(process_state="exiting_after_failure", exception=repr(exc), traceback=traceback.format_exc())
        write_json(out / "launch.json", launch)
        raise


if __name__ == "__main__":
    main()
