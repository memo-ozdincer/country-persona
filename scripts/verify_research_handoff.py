"""Verify a private research snapshot using only Python's standard library."""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = (
    "AGENTS.md", "START_HERE.md", "docs/PROJECT_HANDOFF.md", "docs/HANDOFF_OPERATIONS.md",
    "docs/AURORA_WORKFLOW.md", "configs/posttraining/model.lock.json",
    "scripts/review_deliberation_probe.py", "scripts/run_eval_probe.py",
    "src/country_persona/training_checks.py",
    "data/prepared/evidence-format-20260928-v1/manifest.json",
    "data/prepared/training-readiness-20260928-v1/release.json",
    "data/review/deliberation-999389-combined-assistant-v1/reviews.jsonl",
    "runs/deliberation-999389-base-v1/transcript.jsonl",
    "research/persona-evaluation-20260923/portable-manifest.json",
)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(root):
    root = root.resolve()
    manifest_path = root / "handoff/manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("Manifest must not be a symlink")
    manifest = json.loads(manifest_path.read_text())
    files = manifest["files"]
    if manifest.get("schema_version") != 1 or not files:
        raise ValueError("Unsupported or empty manifest")
    missing_required = set(REQUIRED) - set(files)
    if missing_required:
        raise ValueError("Required artifacts absent: " + ", ".join(sorted(missing_required)))
    errors = []
    for name, entry in files.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            errors.append({"path": name, "error": "unsafe_member_path"})
            continue
        path = root / relative
        if path.resolve() != path or not path.is_file():
            errors.append({"path": name, "error": "missing_or_symlink"})
        elif path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            errors.append({"path": name, "error": "bytes_or_sha256_mismatch"})
    if errors:
        raise ValueError(json.dumps({"verification_failed": errors}))
    return {"status": "all_payload_files_verified", "files": len(files),
            "bytes": sum(item["bytes"] for item in files.values()),
            "manifest_sha256": sha256(manifest_path), "base_commit": manifest["base_commit"],
            "semantic_validation": "not_implied_by_transfer_integrity"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(verify(args.root), indent=2))
