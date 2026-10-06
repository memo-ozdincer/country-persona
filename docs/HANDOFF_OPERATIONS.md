# Verify and continue a research handoff

Read `START_HERE.md`, `AGENTS.md` and [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) first. These are private research snapshots, not public releases.

## Verify the transfer

From the transferred project root, using standard Python:

```bash
python3 scripts/verify_research_handoff.py --root .
git status --short
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier checks every payload file against `handoff/manifest.json`, rejects unsafe paths/symlinks, and checks required entry artifacts. `handoff/git-status.txt` records source working changes, while `handoff/base-history.bundle` preserves committed ancestry. The working files include uncommitted edits and untracked research code. No source commit, push or PR is implied. Base model weights, credentials and runtime environments are excluded; bounded saved LoRA adapters are included.

Snapshot hashes describe transfer time. Intentional later edits will produce mismatches; preserve the original manifest and create a new snapshot after a checkpoint. Do not update hashes merely to silence unexplained differences. Read `handoff/source-inventory.json` before running a builder that needs omitted older corpora.

The environment profile redirects large caches to scratch and supplies a private credential path. Do not display the token, include it in staging, or use another agent's runtime/process without establishing ownership.

## Reproduce existing arithmetic without a GPU

This source-review replay requires only Python's standard library. Choose a fresh output directory:

```bash
PYTHONPATH=src python3 scripts/review_deliberation_probe.py \
  --run runs/deliberation-999389-base-v1 \
  --reviews data/review/deliberation-999389-combined-assistant-v1/reviews.jsonl \
  --output runs/handoff-review-replay-v1
```

Compare its `scores.json` with `data/review/deliberation-999389-combined-assistant-v1/scored/scores.json`. Expected: 42 reviewed responses, 516 unit instances, 366 met/117 unmet/33 unratable, both overall peer gains null, semantic review pending. Absolute script paths in the receipt differ by host; source bytes and arithmetic should match. This tests portability, not independent judging.

Focused engineering tests, once pytest is available:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_deliberation.py tests/test_deliberation_review.py \
  tests/test_policy_eval.py tests/test_evidence_ledger.py
```

Broader tests may need optional dependencies and omitted legacy data. Missing-data failures are not model defects. Consult `pyproject.toml`/`uv.lock`; verify GPU compatibility before installing an ML stack. Keep environments/caches on scratch.

## Next format diagnostic

With the pinned tokenizer environment, first run:

```bash
PYTHONPATH=src python scripts/run_eval_probe.py \
  --pack data/prepared/evidence-format-20260928-v1 \
  --case-cap 9 --max-new-tokens 2048 --context-budget 8192 \
  --preflight-only --output runs/aurora-format-preflight-v1
```

This is tokenizer-only. For actual inference, obtain the exact locked model on scratch, verify bytes, inspect GPU ownership, record the launch, specify `--model-path`, omit `--preflight-only` and choose a fresh output. Expose only the selected available device. The Python runner supports direct single-device inference; the Slurm shell wrapper is Trillium-specific.

After completed inference:

```bash
PYTHONPATH=src python scripts/audit_evidence_format_probe.py \
  --pack data/prepared/evidence-format-20260928-v1 \
  --run runs/aurora-format-base-v1 --output reports/aurora-format-base-v1
```

Those Aurora run paths are planned names, not existing model results. Review all complete outputs against sources. Schema/quote checks do not certify entailment. Inspect this result before another experiment.

## Training and comparison

The [training helper](TRAINING_READINESS_20260928.md) defaults to printing a launch command. Its `--run` path requires Slurm and four GPUs. Aurora had no Slurm commands on PATH during inspection. Establish an explicit Aurora launch path rather than faking scheduler variables; retain model/optimization/reload checks. An H100 scheduler dry run is not Blackwell/NCCL validation.

The checkpoint comparator requires matching device and runtime. An Aurora adapter needs a matched Aurora base run; do not relax this check to mix hosts casually.

## Build the next snapshot

From the authoritative checkout, with Git and selected artifacts available:

```bash
python3 scripts/build_research_handoff.py --output /ABSOLUTE/FRESH/STAGING/DIRECTORY
python3 scripts/verify_research_handoff.py --root /ABSOLUTE/FRESH/STAGING/DIRECTORY
```

The builder refuses existing destinations, selects working files plus relevant ignored artifacts, records omissions, verifies copied bytes and preserves base history/diff/status. It does not upload, allocate, change credentials, commit or push. Transfer to a fresh private workspace and verify there. Never blanket-sync `.env`, credential files, `.venv`, `.git` internals or model caches.

Source PDFs and archived texts are private research context; their inclusion does not create publication permission. Public explorers are presentation layers, not evidence that every local experiment artifact is hosted online. Scratch is non-backed-up: retain durable code/manifests and important outputs elsewhere.

## Private archives larger than a release asset

Growing snapshots retain the full local archive and all historical adapters. If the compressed archive exceeds GitHub's 2 GiB per-asset limit, upload ordered parts below that limit with a JSON multipart manifest and the original verification receipt. The manifest records each part's name, bytes and SHA-256 plus the full archive's name, bytes and SHA-256. Download every part and concatenate in the exact manifest order. Verify every part and the reassembled archive against these fields before extracting, then run the normal payload verifier in the extracted tree.

`scripts/upload_private_handoff.py --asset-manifest /ABSOLUTE/MULTIPART-MANIFEST.json` checks part hashes, ordered reassembly and the original archive/receipt/commit binding before creating a release. It verifies the destination repository is private and checks GitHub's returned SHA-256/size for every uploaded asset. The full archive remains available locally; splitting does not omit payload files or reduce the evidence included.
