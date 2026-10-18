"""Package only the eight owned October 18 run directories, not a full snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

RUNS = ["scenario-base-sequence-20261018-v1", "scenario-base-native-20261018-v1",
        "scenario-native-boundary-preflight-20261018-v1", "scenario-base-native-boundary-20261018-v1",
        "scenario-fit128-20261018-v1", "scenario-adapter-fitting-20261018-v1",
        "scenario-adapter-held-20261018-v1", "scenario-adapter-native-boundary-20261018-v1"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--assets", type=Path, required=True)
    a = p.parse_args()
    if any(x.exists() for x in [a.archive, a.manifest, a.receipt, a.assets]):
        raise ValueError("Fresh delivery paths required")
    root = Path.cwd().resolve()
    files = []
    for name in RUNS:
        run = root / "runs" / name
        launch = json.loads((run / "launch.json").read_text())
        if launch["status"] not in {"completed", "preflight_complete"}:
            raise ValueError("A run is incomplete: " + name)
        if name == "scenario-fit128-20261018-v1" and launch.get("process_state") != "exiting_normally":
            raise ValueError("Release the owned resident process before packaging")
        if (run / "evaluation-result.json").exists():
            measured = json.loads((run / "evaluation-result.json").read_text())
            if sha(run / "responses.jsonl") != measured["responses_sha256"]:
                raise ValueError("Transcript differs from its original completion receipt")
        if (run / "training-result.json").exists():
            measured = json.loads((run / "training-result.json").read_text())
            if sha(run / "optimization.jsonl") != measured["trace_sha256"]:
                raise ValueError("Optimizer trace differs from its original completion receipt")
            for file, expected in measured["serialization"]["files_sha256"].items():
                if sha(run / "adapter" / file) != expected:
                    raise ValueError("Adapter differs from its original save verification")
        files.extend(f for f in run.rglob("*") if f.is_file())
        if run.with_suffix(".log").exists():
            files.append(run.with_suffix(".log"))
    for f in files:
        if f.is_symlink() or f.stat().st_size > 256 * 1024**2 or ".env" in f.name:
            raise ValueError("Unexpected payload type, size or credential file")
    if sum(f.stat().st_size for f in files) > 256 * 1024**2:
        raise ValueError("Checkpoint exceeded its bounded scope")
    manifest = {str(f.relative_to(root)): dict(bytes=f.stat().st_size, sha256=sha(f)) for f in sorted(files)}
    with tarfile.open(a.archive, "w:gz", compresslevel=6, dereference=True) as archive:
        for f in sorted(files):
            archive.add(f, arcname=str(f.relative_to(root)), recursive=False)
    verified = []
    with tarfile.open(a.archive, "r:gz") as archive:
        members = archive.getmembers()
        if {m.name for m in members} != set(manifest) or len(members) != len(manifest):
            raise ValueError("Archive inventory differs")
        for member in members:
            if not member.isfile() or Path(member.name).is_absolute() or ".." in Path(member.name).parts:
                raise ValueError("Unsafe archive path/type")
            h = hashlib.sha256()
            with archive.extractfile(member) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            if member.size != manifest[member.name]["bytes"] or h.hexdigest() != manifest[member.name]["sha256"]:
                raise ValueError("Archive payload differs")
            verified.append(member.name)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    payload = dict(status="bounded_new_run_payload_verified", source_commit=source,
        original_v47_manifest_sha256="fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b",
        files=manifest, archive=dict(name=a.archive.name, bytes=a.archive.stat().st_size, sha256=sha(a.archive)),
        exclusions="Base weights, credentials, caches, unrelated processes/runs and immutable old snapshots are not included.",
        restore="Verify asset digests; extract into a fresh empty directory. Combine with the pinned v47 snapshot and committed Git overlay; never overwrite historical stages.")
    a.manifest.write_text(json.dumps(payload, indent=2) + "\n")
    a.receipt.write_text(json.dumps(dict(status="all_archive_members_rehashed_and_verified", files=len(verified),
        archive=payload["archive"], manifest_sha256=sha(a.manifest), source_commit=source), indent=2) + "\n")
    a.assets.write_text(json.dumps(dict(assets=[dict(path=str(f.resolve()), bytes=f.stat().st_size, sha256=sha(f))
        for f in [a.archive, a.manifest, a.receipt]]), indent=2) + "\n")
    print(json.dumps(dict(files=len(verified), archive_bytes=a.archive.stat().st_size, archive_sha256=sha(a.archive))))


if __name__ == "__main__":
    main()
