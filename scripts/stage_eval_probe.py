"""Stage a frozen inference pack and its reusable allocation; no remote writes."""
import argparse
import json
from pathlib import Path
import shutil

from country_persona.io import sha256, write_json


def stage(destination, pack=Path("data/prepared/eval-pilot-20260927/probe-v1")):
    if destination.exists():
        raise ValueError("Choose a fresh staging directory")
    lock_path = Path("configs/posttraining/model.lock.json")
    lock = json.loads(lock_path.read_text())
    pack_manifest = json.loads((pack / "manifest.json").read_text())
    paths = [Path(p) for p in ("scripts/run_eval_probe.py", "scripts/trillium_eval_probe.sbatch",
                               "scripts/trillium_eval_probe.sh",
                               "src/country_persona/__init__.py", "src/country_persona/inference_probe.py",
                               "src/country_persona/action_eval.py", "src/country_persona/io.py",
                               "reports/trillium_model_verification.json")]
    paths += [lock_path, pack / "manifest.json", pack / "cases.jsonl"]
    # Gold references and raw documents are deliberately unnecessary for inference.
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Tokenizer/config lock mismatch")
        paths.append(Path(item["path"]))
    if sha256(pack / "cases.jsonl") != pack_manifest["files_sha256"]["cases.jsonl"]:
        raise ValueError("Frozen probe changed")
    files = {str(p): sha256(p) for p in paths}
    destination.mkdir(parents=True)
    for path in paths:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        if sha256(target) != files[str(path)]:
            raise ValueError("Staged copy differs from its source")
    report = {"status": "local_payload_prepared_not_submitted", "files_sha256": files,
              "bytes": sum((destination / p).stat().st_size for p in files),
              "planned_account": "def-zhijing", "planned_gpu_count": 1,
              "planned_wall_cap_minutes": 180, "maximum_requested_gpu_hours": 3,
              "allocation_lifetime": "sleep infinity, bounded by Slurm wall time; experiments are separate steps",
              "scheduler_validation": "pending sbatch --test-only",
              "production_generations": 0}
    write_json(destination / "staging-manifest.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/eval-pilot-20260927/probe-v1"))
    args = parser.parse_args()
    result = stage(args.output, args.pack)
    print(f"Staged {len(result['files_sha256'])} files, {result['bytes']} bytes. No remote writes or job submission.")
