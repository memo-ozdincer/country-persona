"""Prepare an isolated local GPU handoff; never submit or launch a job."""
import argparse
import json
from pathlib import Path
import shutil

from country_persona.io import sha256, write_json


def stage(output):
    if output.exists():
        raise ValueError("Use a fresh staging directory")
    training = Path("data/prepared/training-readiness-20260928-v1")
    deliberation = Path("data/prepared/deliberation-probe-20260928-v1")
    paths = [Path(p) for p in (
        "scripts/launch_training_readiness.py", "scripts/trillium_training_allocation.sbatch", "scripts/trillium_readiness_step.sh",
        "scripts/run_deliberation_probe.py", "scripts/run_eval_probe.py", "scripts/trillium_eval_probe.sh",
        "src/country_persona/__init__.py", "src/country_persona/train.py", "src/country_persona/training_checks.py", "src/country_persona/io.py",
        "src/country_persona/inference_probe.py", "src/country_persona/action_eval.py", "src/country_persona/deliberation.py",
        "configs/posttraining/model.lock.json", "configs/posttraining/readiness-20260928.json",
        "reports/trillium_model_verification.json", "docs/TRAINING_READINESS_20260928.md", "pyproject.toml", "uv.lock")]
    lock = json.loads(Path("configs/posttraining/model.lock.json").read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Changed locked tokenizer")
        paths.append(Path(item["path"]))
    for directory, manifest_name, names in (
        (training, "release.json", ["smoke.train.jsonl", "smoke.train.manifest.jsonl", "fit-probe.train.jsonl", "fit-probe.train.manifest.jsonl"]),
        (deliberation, "manifest.json", ["scenarios.jsonl", "protocol.json"]),
        (Path("data/prepared/eval-pilot-20260927/two-event-v1"), "manifest.json", ["cases.jsonl"]),
    ):
        manifest = json.loads((directory / manifest_name).read_text())
        paths.append(directory / manifest_name)
        for name in names:
            path = directory / name
            if sha256(path) != manifest["files_sha256"][name]:
                raise ValueError("Prepared file changed: " + str(path))
            paths.append(path)
    # Gold review references stay local; inference and training need no answer key.
    files = {str(p): sha256(p) for p in paths}
    output.mkdir(parents=True)
    for source in paths:
        target = output / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256(target) != files[str(source)]:
            raise ValueError("Copy mismatch")
    receipt = {"status": "local_payload_prepared_not_uploaded_or_submitted", "files_sha256": files,
               "bytes": sum(p.stat().st_size for p in paths), "account": "def-zhijing", "gpus": 4,
               "maximum_allocation_gpu_hours": 4, "allocation_lifetime": "sleep infinity within 1h Slurm wall limit",
               "scheduler_validation": "pending", "cuda_nccl_validation": "pending", "evaluation_first_gate": "pending"}
    write_json(output / "staging-manifest.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = stage(args.output)
    print(f"Staged {len(result['files_sha256'])} files ({result['bytes']} bytes); no job submitted.")
