"""Capture actual working files and bounded research artifacts; never credentials or base weights."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from verify_research_handoff import REQUIRED, sha256, verify

CODE_TREES = ("src", "scripts", "tests", "configs", "docs", "reports", "research",
              "explorer", "country_persona_playbook", "data/curation", "data/manifests")
PREPARED = ("decision-cases-20260914", "decision-posttraining-20260916",
            "eval-pilot-20260926", "eval-pilot-20260927", "eval-qwen3-v1", "eval-v1",
            "policy-workshop-20260916", "deliberation-probe-20260928-v1",
            "evidence-format-20260928-v1", "synthesis-diagnostic-20260928-v1",
            "training-readiness-20260928-v1", "qwen35-smoke-20260930-v1",
            "qwen35-scope-fit-20260930-v1", "qwen35-conflict-fit-20260930-v1",
            "qwen35-plan-to-text-eval-20260930-v1", "qwen35-plan-to-text-eval-20260930-v2",
            "qwen35-plan-to-text-fit-20260930-v1", "qwen35-benchmark-plan-20260930-v1",
            "qwen35-source-plan-probe-20261002-v1", "qwen35-source-plan-repair-20261002-v1",
            "source-application-sft-20261003-v1", "source-application-sft-20261003-v2",
            "source-application-eval-20261003-v1", "source-application-eval-20261003-v2",
            "coverage-objective-20261003-v1", "source-preference-20261003-v1",
            "minimal-country-20261005-v1", "minimal-country-20261005-v2",
            "minimal-mechanism-20261005-v1", "minimal-country-transfer-20261005-v1",
            "minimal-country-transfer-20261005-v2", "minimal-deliberation-initials-20261006-v1",
            "minimal-deliberation-revisions-20261006-v1", "minimal-deliberation-synthesis-20261006-v1",
            "minimal-deliberation-adapted-aggregator-20261006-v1",
            "minimal-attribution-ledger-20261006-v1", "minimal-attribution-ledger-20261006-v2",
            "minimal-synthesis-fit-20261006-v1", "minimal-synthesis-fit-20261006-v2",
            "minimal-synthesis-cold-20261006-v1",
            "synthesis-rehearsal-20261006-v1", "synthesis-rehearsal-wps-20261006-v1",
            "rehearsal-diagnostic-20261006-v1", "native-reasoning-20261006-v1",
            "native-sampling-20261006-v1", "native-sampling-20261006-v2",
            "country-source-cards-20261006-v1", "country-source-cards-20261006-v2",
            "country-source-bridge-20261006-v1", "factual-anchor-20261006-v1",
            "factual-repair-20261006-v1", "factual-repair-20261006-v1-parent",
            "raw-coverage-20261006-v1", "raw-update-status-20261006-v1",
            "raw-update-status-20261006-v1-parent", "repaired-state-20261006-v1",
            "repaired-state-partial-eval-20261006-v1",
            "application-paragraph-20261006-v1-parent", "application-paragraph-20261006-v1-combined",
            "application-paragraph-20261006-v1-chosen", "application-paragraph-20261006-v2-parent",
            "application-paragraph-20261006-v2-combined", "application-paragraph-20261006-v2-chosen",
            "two-episode-20261006-v1", "two-episode-sanctions-eval-20261006-v1",
            "minimal-endorsement-20261006-v1", "endorsement-authority-eval-20261006-v1",
            "conditional-india-20261006-v1", "conditional-india-eval-20261006-v1",
            "conditional-india-20261006-v2", "conditional-india-eval-20261006-v2",
            "conditional-india-fit-20261006-v2", "haiti-source-scope-20261006-v1",
            "diverse-country-20261006-v1", "diverse-country-20261006-v2",
            "diverse-country-fit-20261006-v2", "diverse-country-role-check-20261006-v1",
            "two-context-country-20261006-v1", "two-context-country-base-20261006-v1",
            "two-context-country-parent-20261006-v1", "two-context-country-fit-20261006-v1",
            "two-context-source-facts-20261006-v1",
            "model-generated-plan-planner-20261006-v1", "model-generated-plan-writer-20261006-v1",
            "model-decision-plan-planner-20261006-v1", "question-guided-plan-planner-20261006-v1",
            "question-guided-plan-writer-20261006-v1", "plan-input-20261006-v1",
            "plan-input-fit-20261006-v1", "ordinary-points-20261006-v1",
            "ordinary-points-20261006-v2", "compression-teacher-20261006-v1",
            "compression-teacher-probe-20261006-v1", "compression-teacher-remaining-20261006-v1",
            "compression-student-draft-20261006-v2", "compression-checkpoint-20261006-v1",
            "compression-parent-controls-20261006-v1", "compression-fit-20261006-v1",
            "compression-points-only-20261007-v1", "compact-points-20261007-v1",
            "compact-points-20261007-v2")
RAW = ("country-extension-20260914", "country-knowledge-20260914", "country-expansion-20260913",
       "decision-cases-20260914", "eval-pilot-primary-checks-20260926", "eval-sources-20260927",
       "ledger-eval-sources-20260928", "ledger-eval-sources-20260928-expansion",
       "unbench-audit-20260926", "unsc-bench-audit-20260926",
       "benchmark-plan-grounding-20260930-v1", "benchmark-plan-grounding-20260930-v2",
       "benchmark-plan-grounding-20260930-v3", "source-plan-grounding-20261002-v1",
       "source-application-grounding-20261003-v1", "coverage-objective-grounding-20261003-v1",
       "conditional-india-haiti-grounding-20261006-v1", "diverse-country-somalia-grounding-20261006-v1",
       "two-context-training-grounding-20261006-v1", "two-context-sudan-grounding-20261006-v1",
       "plan-input-icc-grounding-20261006-v1", "compression-libya-grounding-20261006-v1")
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".cache"}
SECRET = re.compile(rb"hf_[A-Za-z0-9]{20,}|-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----")
QUOTED_KEY_HEADER = re.compile(
    rb"(?P<quote>'|\"|\\\")-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----(?P=quote)"
)
REFERENCE_ADAPTERS = {
    "runs/open-character-humor-reproduction-20261004-v1/dpo-fit/adapter/adapter_model.safetensors",
    "runs/open-character-humor-reproduction-20261004-v1/sft-fit/adapter/adapter_model.safetensors",
}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def selected_files(root):
    names = {name for name in git(root, "ls-files", "-z").decode().split("\0") if name}
    for tree in CODE_TREES:
        names.update(str(p.relative_to(root)) for p in (root / tree).rglob("*") if p.is_file())
    for p in root.iterdir():
        if p.is_file() and p.suffix in {".md", ".toml", ".lock"}:
            names.add(p.name)
    for p in (root / "data").glob("*.json"):
        names.add(str(p.relative_to(root)))
    trees = ["data/review", "data/metadata/qwen3-8b-tokenizer"]
    trees += ["data/prepared/" + name for name in PREPARED]
    trees += ["data/raw/" + name for name in RAW]
    for p in (root / "runs").iterdir():
        if p.is_dir() and "staging" not in p.name and "handoff" not in p.name:
            trees.append(str(p.relative_to(root)))
        elif p.is_dir() and "staging" in p.name:
            # Preserve staging receipts, not duplicate tokenizers/code for every historical payload.
            names.update(str(f.relative_to(root)) for f in p.glob("*-manifest.json"))
    for tree in trees:
        names.update(str(p.relative_to(root)) for p in (root / tree).rglob("*") if p.is_file())
    # Retain coverage/manifests and bounded Reddit examples, not the multi-GB text exports.
    reddit = root / "data/prepared/reddit-country-20260923"
    names.update(str(p.relative_to(root)) for p in reddit.rglob("*")
                 if p.is_file() and (p.name.endswith("audit-sample.jsonl.gz") or
                                    (p.suffix in {".json", ".md", ".html"} and p.stat().st_size < 10_000_000)))
    result = []
    for name in sorted(names):
        p = root / name
        parts = Path(name).parts
        if set(parts) & SKIP_PARTS or p.name.endswith((".pyc", ".part")) or p.name == ".DS_Store":
            continue
        if p.name.startswith(".env") or "secrets" in parts or p.suffix in {".pem", ".key"}:
            raise ValueError("Credential-like path in selection: " + name)
        if not p.exists():  # Preserve working-tree deletions in the diff, not stale HEAD copies.
            continue
        if p.resolve() != p or not p.is_file():
            raise ValueError("Refusing symlink/nonregular source: " + name)
        if p.stat().st_size > 300_000_000:
            # This arm's rank-64 BF16 LoRA is approximately 323 MB. Preserve its exact
            # fitted weights in the private handoff, with a narrow size/type/rank guard.
            if name not in REFERENCE_ADAPTERS or p.stat().st_size > 350_000_000:
                raise ValueError("Unexpected large member; review inclusion: " + name)
            adapter_config = json.loads((p.parent / "adapter_config.json").read_text())
            if (adapter_config.get("peft_type"), adapter_config.get("r"), adapter_config.get("lora_alpha")) != ("LORA", 64, 128):
                raise ValueError("Large reference member is not the expected fitted LoRA: " + name)
        result.append(name)
    if set(REQUIRED) - set(result):
        raise ValueError("Required handoff material missing: " + str(sorted(set(REQUIRED) - set(result))))
    return result


def inventory(root, names):
    selected = set(names)
    result = []
    for tree in ("data/raw", "data/canonical", "data/prepared", "data/review", "runs"):
        for p in sorted((root / tree).iterdir()) if (root / tree).exists() else []:
            if p.is_symlink():
                continue
            files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and not f.is_symlink()]
            included = [f for f in files if str(f.relative_to(root)) in selected]
            result.append({"path": str(p.relative_to(root)), "source_files": len(files),
                           "source_bytes": sum(f.stat().st_size for f in files),
                           "included_files": len(included), "included_bytes": sum(f.stat().st_size for f in included),
                           "coverage": "complete" if len(included) == len(files) else "partial" if included else "omitted"})
    return result


def build(root, output, reuse_snapshot=None):
    root, output = root.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Choose a fresh staging directory")
    names = selected_files(root)
    inv = inventory(root, names)
    source_hashes = {name: sha256(root / name) for name in names}
    prior_files, prior_manifest_sha256, reused = {}, None, 0
    if reuse_snapshot is not None:
        reuse_snapshot = reuse_snapshot.resolve()
        if reuse_snapshot == root or reuse_snapshot == output:
            raise ValueError("Reuse only a separate frozen snapshot, never the working source")
        prior_manifest = reuse_snapshot / "handoff/manifest.json"
        prior = json.loads(prior_manifest.read_text())
        if prior["credentials_included"] or prior["base_model_weights_included"]:
            raise ValueError("Unexpected prior snapshot scope")
        prior_files = prior["files"]
        prior_manifest_sha256 = sha256(prior_manifest)
    output.mkdir(parents=True, mode=0o700)
    for name in names:
        source, target = root / name, output / name
        # Secrets must not enter copied docs/code or raw text. Do not print matched data.
        if source.suffix.lower() not in {".pdf", ".zip", ".gz", ".safetensors", ".bin", ".pt", ".png", ".jpg"}:
            # A quoted header alone (e.g. a Python PEM parser's b'BEGIN...')
            # contains no private-key material. A header followed by a key body
            # before its closing quote remains subject to the secret check.
            if SECRET.search(QUOTED_KEY_HEADER.sub(b"[KEY_HEADER_LITERAL]", source.read_bytes())):
                raise ValueError("Possible secret detected; file excluded by failing build: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = reuse_snapshot / name if reuse_snapshot is not None else None
        expected = prior_files.get(name)
        if expected is not None and expected["sha256"] == source_hashes[name]:
            if previous.resolve() != previous or not previous.is_file():
                raise ValueError("Refusing nonregular prior snapshot member: " + name)
            if previous.stat().st_size != expected["bytes"] or sha256(previous) != source_hashes[name]:
                raise ValueError("Prior snapshot member changed: " + name)
            # Link immutable snapshot bytes, never mutable working-tree files.
            os.link(previous, target)
            reused += 1
        else:
            shutil.copy2(source, target)
        if sha256(target) != source_hashes[name] or sha256(source) != source_hashes[name]:
            raise ValueError("Source changed during snapshot: " + name)
    meta = output / "handoff"
    meta.mkdir(mode=0o700)
    (meta / "source-inventory.json").write_text(json.dumps(inv, indent=2) + "\n")
    (meta / "git-status.txt").write_bytes(git(root, "status", "--short"))
    (meta / "working-tree.patch").write_bytes(git(root, "diff", "--binary", "HEAD"))
    base = git(root, "rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "-C", str(root), "bundle", "create", str(meta / "base-history.bundle"), "HEAD"], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    members = names + [str(p.relative_to(output)) for p in meta.iterdir() if p.is_file()]
    manifest = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                "source_root": str(root), "base_commit": base,
                "source_remote": "https://github.com/memo-ozdincer/country-persona.git",
                "kind": "private_working_state_snapshot_not_a_training_or_public_release",
                "credentials_included": False, "base_model_weights_included": False,
                "immutable_prior_snapshot_members_reused": reused,
                "reuse_snapshot_manifest_sha256": prior_manifest_sha256,
                "omissions": ["Credentials and virtual environments", "Base model weights and caches",
                              "Large Reddit raw/body exports and older bulk/canonical corpora; see source-inventory.json",
                              "Duplicated historical staging payloads; their manifests are retained"],
                "files": {name: {"bytes": (output / name).stat().st_size, "sha256": sha256(output / name)}
                          for name in sorted(members)}}
    (meta / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return verify(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-snapshot", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.output, args.reuse_snapshot), indent=2))
