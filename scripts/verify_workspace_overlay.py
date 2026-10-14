"""Verify a Git update over a pinned, immutable research handoff (CPU only)."""
import argparse
import json
from pathlib import Path
import subprocess

from verify_research_handoff import REQUIRED, sha256


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def verify(root, manifest_sha256):
    root = root.resolve()
    manifest_path = root / "handoff/manifest.json"
    if manifest_path.is_symlink() or sha256(manifest_path) != manifest_sha256:
        raise ValueError("Snapshot manifest differs from the independently pinned digest")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1 or not set(REQUIRED) <= set(manifest["files"]):
        raise ValueError("Invalid or incomplete snapshot manifest")
    base = manifest["base_commit"]
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, "HEAD"], check=True)
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("Commit or preserve working changes before verifying the Git overlay")
    base_tracked = set(git(root, "ls-tree", "-r", "--name-only", "-z", base).decode().split("\0"))
    changed = set(git(root, "diff", "--name-only", "-z", base, "HEAD").decode().split("\0"))
    tracked = {}
    for row in git(root, "ls-files", "--stage", "-z").decode().split("\0"):
        if not row:
            continue
        metadata, name = row.split("\t", 1)
        mode, oid, stage = metadata.split()
        if mode not in {"100644", "100755"} or stage != "0":
            raise ValueError("Nonregular or unmerged tracked file: " + name)
        tracked[name] = oid
    overlays = []
    original = 0
    for name, entry in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("Unsafe snapshot member: " + name)
        path = root / relative
        if path.resolve() != path or not path.is_file():
            raise ValueError("Missing or symlinked snapshot member: " + name)
        if name in base_tracked and name in changed:
            if name not in tracked:
                raise ValueError("Snapshot payload deletion requires a new full handoff: " + name)
            overlays.append(name)
        else:
            if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
                raise ValueError("Unexplained payload change: " + name)
            original += 1
    # Rehash Git content too: a clean index alone can trust cached file stat data.
    for name, oid in tracked.items():
        path = root / name
        if path.resolve() != path or not path.is_file():
            raise ValueError("Missing or symlinked Git file: " + name)
        actual = git(root, "hash-object", "--no-filters", "--", name).decode().strip()
        if actual != oid:
            raise ValueError("Git working bytes differ from the committed blob: " + name)
    return {
        "status": "snapshot_payload_and_committed_overlay_verified",
        "snapshot_manifest_sha256": manifest_sha256,
        "snapshot_base_commit": base,
        "workspace_commit": git(root, "rev-parse", "HEAD").decode().strip(),
        "unchanged_snapshot_files": original,
        "intentional_committed_overlays": sorted(overlays),
        "tracked_files_verified": len(tracked),
        "new_tracked_files": sorted(set(tracked) - set(manifest["files"])),
        "limitations": "Byte integrity only; no semantic review or underlying storage health certification.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest-sha256", required=True,
                        help="Pin from a separately verified release receipt, not the local manifest itself.")
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.manifest_sha256), indent=2))
