# Country Persona: session instructions

Read `START_HERE.md`, then `docs/PROJECT_HANDOFF.md` before experiments. Current summaries guide navigation; dated reports remain the evidence. This tree includes substantial uncommitted work. A clean clone alone does not reproduce it. Preserve existing changes and Germany/China releases.

## User requirements

- Model dated country–institution–role behavior and source-faithful international-policy deliberation. Governments, populations and Reddit communities are different targets.
- Stabilize evaluation before substantive training. Distinguish software checks, assistant annotations, independent review and actual model-quality results.
- Every small run must answer a concrete question, leave an inspectable artifact and inform the next decision. Inspect it before launching the next. No speculative experiment queues or multi-seed sweeps at this stage.
- The active extension is FRA/GBR/IND/BRA. Preserve the user's Germany/China decision-case work.
- On Aurora, a medical agent may also use `memo`. **Never cancel or alter unfamiliar jobs/processes, even under our username.** Manage only resources positively linked to this project's launch records. Record host, GPU UUIDs, PID/job identity, process start time, command and run directory; recheck identity before termination. No account-wide cleanup on Aurora.
- Put models, caches and bulky outputs under `/mfs1/u/memo/country-persona-research`, not CSlab home. `/aurora` was not writable by `memo`; do not alter disks or permissions.
- On Trillium prefer `def-zhijing`; retained allocations use `sleep infinity` within wall limits, with experiments as separate steps. Past job IDs/deadlines are historical. September 29's one-time account-wide cancellation is not standing authorization.
- Credentials stay outside the repo. On Aurora source `/h/405/memo/.config/country-persona/aurora-env.sh` for private `HF_TOKEN_PATH` and scratch caches. Never print, commit or put the token value in command arguments.

## Current boundary

The 42-call base deliberation baseline and six-call synthesis diagnostic completed on Trillium. All 42 baseline outputs have one assistant's provisional review; 33 rating instances remain unratable and independent review is pending. No new four-country production training has run. An older Germany/China adapter ran and regressed; do not claim training has never run.

The next prepared diagnostic is nine synthesis calls across three contexts and three formats. It is unrun. Tiny CPU masking/optimization/reload checks pass; Aurora CUDA/NCCL training is unverified. Authored fixtures, tokenizer preflights and scheduler dry runs are not model-quality experiments.

## Reproducibility

- Preserve frozen packs, transcripts, source spans, hashes and failed-run receipts. Use fresh output directories.
- Verify transferred snapshots with `python3 scripts/verify_research_handoff.py --root .`. The manifest distinguishes included files from omitted corpora; credentials and base weights are excluded.
- Model: `Qwen/Qwen3-8B`, revision `b968826d9c46dd6066d109eabc6255188de91218`, thinking disabled. Changes require explicit versioned comparisons.
- The training launch helper is Slurm-specific. Do not fake `SLURM_JOB_ID` on Aurora; establish an explicit launch path before training.
- Before/after comparison requires matching GPU type, versions, inference code and protocol. Establish an Aurora base run for an Aurora adapter comparison; H100 results are historical diagnostics.
- After each meaningful checkpoint, update the state summary and evidence receipt. Refresh snapshots with working changes and ignored artifacts; a Git push alone does not transfer these.
