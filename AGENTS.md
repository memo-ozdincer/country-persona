# Country Persona: session instructions

Read `START_HERE.md`, then `docs/PROJECT_HANDOFF.md` before experiments. Current summaries guide navigation; dated reports remain the evidence. This tree includes substantial uncommitted work. A clean clone alone does not reproduce it. Preserve existing changes and Germany/China releases.

## User requirements

- Model dated country–institution–role behavior and source-faithful international-policy deliberation. Governments, populations and Reddit communities are different targets.
- Stabilize evaluation before substantive training. Distinguish software checks, assistant annotations, independent review and actual model-quality results.
- The September 30 priority is small Aurora training tests using Qwen3.5 at 8B or smaller. A separately locked 4B technical smoke passed; a large inference campaign or the old nine-call diagnostic is not required before another technical test.
- Every small run must answer a concrete question, leave an inspectable artifact and inform the next decision. Inspect it before launching the next. No speculative experiment queues or multi-seed sweeps at this stage.
- The active extension is FRA/GBR/IND/BRA. Preserve the user's Germany/China decision-case work.
- On Aurora, a medical agent may also use `memo`. **Never cancel or alter unfamiliar jobs/processes, even under our username.** Manage only resources positively linked to this project's launch records. Record host, GPU UUIDs, PID/job identity, process start time, command and run directory; recheck identity before termination. No account-wide cleanup on Aurora.
- Put models, caches and bulky outputs under `/mfs1/u/memo/country-persona-research`, not CSlab home. `/aurora` was not writable by `memo`; do not alter disks or permissions.
- On Trillium prefer `def-zhijing`; retained allocations use `sleep infinity` within wall limits, with experiments as separate steps. Past job IDs/deadlines are historical. September 29's one-time account-wide cancellation is not standing authorization.
- Credentials stay outside the repo. On Aurora source `/h/405/memo/.config/country-persona/aurora-env.sh` for private `HF_TOKEN_PATH` and scratch caches. Never print, commit or put the token value in command arguments.

## Current boundary

The 42-call base deliberation baseline and six-call synthesis diagnostic completed on Trillium. All 42 baseline outputs have one assistant's provisional review; 33 rating instances remain unratable and independent review is pending. No new four-country production training has run. An older Germany/China adapter ran and regressed; do not claim training has never run.

The prepared nine-call synthesis diagnostic remains unrun. On September 30, Qwen3.5-4B completed a single-GPU Aurora BF16 LoRA smoke: four examples, two optimizer steps, finite gradients, 496 changed adapter tensors and exact save/reload. Four matched baseline/adapter controls were inspected; they are training prompts, not a persona-quality evaluation. NCCL/distributed training and independent review remain unverified. See `docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md` and its measured receipt.

## Reproducibility

- Preserve frozen packs, transcripts, source spans, hashes and failed-run receipts. Use fresh output directories.
- Verify transferred snapshots with `python3 scripts/verify_research_handoff.py --root .`. The manifest distinguishes included files from omitted corpora; credentials and base weights are excluded.
- Historical evaluation model: `Qwen/Qwen3-8B`, revision `b968826d9c46dd6066d109eabc6255188de91218`, thinking disabled. Preserve its lock/results. The user-authorized Qwen3.5 technical checkpoint has its own model/runtime lock in `configs/posttraining/qwen35-smoke-20260930.json`; changes require explicit versioned comparisons.
- The historical training launch helper is Slurm-specific. Do not fake `SLURM_JOB_ID` on Aurora. `scripts/run_aurora_qwen35_smoke.py` is the verified explicit single-GPU Aurora path with fresh outputs, byte verification and ownership records.
- Before/after comparison requires matching GPU type, versions, inference code and protocol. Establish an Aurora base run for an Aurora adapter comparison; H100 results are historical diagnostics.
- After each meaningful checkpoint, update the state summary and evidence receipt. Refresh snapshots with working changes and ignored artifacts; a Git push alone does not transfer these.
