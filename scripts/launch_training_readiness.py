"""Print the pinned GPU command; only explicit --run executes an optimization probe."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from country_persona.io import sha256
from country_persona.train import validated_export


def command(recipe, output, model_path, config_path=Path("configs/posttraining/readiness-20260928.json")):
    config = json.loads(config_path.read_text())
    lock_path = Path("configs/posttraining/model.lock.json")
    lock = json.loads(lock_path.read_text())
    root = Path(config["dataset"])
    release = json.loads((root / "release.json").read_text())
    if release["model_lock_sha256"] != sha256(lock_path):
        raise ValueError("Prepared data uses a different model lock")
    for name, value in release["files_sha256"].items():
        if sha256(root / name) != value:
            raise ValueError("Prepared training data changed")
    settings = config["recipes"][recipe]
    data = root / (settings["dataset"] + ".jsonl")
    manifest = root / (settings["dataset"] + ".manifest.jsonl")
    validated_export(data, manifest, "train", allow_research=True)
    if Path(output).exists():
        raise ValueError("Choose a fresh output directory")
    defaults = config["defaults"]
    return [sys.executable, "-m", "torch.distributed.run", "--standalone", f"--nproc_per_node={config['world_size']}",
            "--module", "country_persona.train", "--model", str(model_path), "--revision", lock["revision"],
            "--research-prepared", "--data", str(data), "--manifest", str(manifest), "--output", str(output),
            "--max-length", str(defaults["max_length"]), "--rank", str(defaults["rank"]),
            "--lr", str(defaults["learning_rate"]), "--seed", str(defaults["seed"]),
            "--grad-accum", str(settings["gradient_accumulation"]), "--max-steps", str(settings["max_steps"]),
            "--warmup-ratio", str(settings["warmup_ratio"])]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", choices=("smoke", "fit-probe"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-path", type=Path, default=Path("/scratch/memoozd/models/Qwen3-8B-Instruct"))
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    cmd = command(args.recipe, args.output, args.model_path)
    print(shlex.join(cmd), flush=True)
    if args.run:
        import torch
        from country_persona.inference_probe import verify_snapshot
        expected_world = json.loads(Path("configs/posttraining/readiness-20260928.json").read_text())["world_size"]
        if not os.environ.get("SLURM_JOB_ID") or torch.cuda.device_count() != expected_world:
            raise RuntimeError(f"Run inside an explicit {expected_world}-GPU Slurm step")
        lock = json.loads(Path("configs/posttraining/model.lock.json").read_text())
        receipt = json.loads(Path("reports/trillium_model_verification.json").read_text())
        verify_snapshot(args.model_path, lock, receipt)
        env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false"}
        subprocess.run(cmd, check=True, env=env)
