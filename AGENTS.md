# Country Persona: session instructions

Read `START_HERE.md`, then `docs/PROJECT_HANDOFF.md` before experiments. Current summaries guide navigation; dated reports remain the evidence. This tree includes substantial uncommitted work. A clean clone alone does not reproduce it. Preserve existing changes and Germany/China releases.

## User requirements

- Model dated country–institution–role behavior and source-faithful international-policy deliberation. Governments, populations and Reddit communities are different targets.
- Stabilize evaluation before substantive training. Distinguish software checks, assistant annotations, independent review and actual model-quality results.
- The September 30 priority is small Aurora training tests using Qwen3.5 at 8B or smaller. A separately locked 4B technical smoke passed; a large inference campaign or the old nine-call diagnostic is not required before another technical test.
- Every small run must answer a concrete question, leave an inspectable artifact and inform the next decision. Inspect it before launching the next. No speculative experiment queues or multi-seed sweeps at this stage.
- Small scope is for getting results that guide action, not stopping after plumbing passes. Continue from inspected results: change supervision or methods, fix errors, research or replan as warranted. Aurora uses NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs; retain the exact hardware name in comparisons.
- The active extension is FRA/GBR/IND/BRA. Preserve the user's Germany/China decision-case work.
- On Aurora, a medical agent may also use `memo`. **Never cancel or alter unfamiliar jobs/processes, even under our username.** Manage only resources positively linked to this project's launch records. Record host, GPU UUIDs, PID/job identity, process start time, command and run directory; recheck identity before termination. No account-wide cleanup on Aurora.
- Put models, caches and bulky outputs under `/mfs1/u/memo/country-persona-research`, not CSlab home. `/aurora` was not writable by `memo`; do not alter disks or permissions.
- On Trillium prefer `def-zhijing`; retained allocations use `sleep infinity` within wall limits, with experiments as separate steps. Past job IDs/deadlines are historical. September 29's one-time account-wide cancellation is not standing authorization.
- Credentials stay outside the repo. On Aurora source `/h/405/memo/.config/country-persona/aurora-env.sh` for private `HF_TOKEN_PATH` and scratch caches. Never print, commit or put the token value in command arguments.

## Current boundary — 19 October 2026

Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md), then the dated evidence. Latest evaluation: [docs/GROUNDED_ROLE_CHECKPOINT_20261019.md](docs/GROUNDED_ROLE_CHECKPOINT_20261019.md). Eleven generated records (ten public statements/one fact map), all hand-read, zero updates. Same pre-target India/UK dossier with requested-role-only differences. Full base and saved four-speech adapter both fail; compact quote cards remove a clear cross-country mix-up but leave recipient/coverage errors. An unedited base-extracted map gives 18/18 material units and one provisional UK strict pass; India exceeds the word limit and adds an uncertain explanation. A smaller word target fixes length but regresses proposal/authority/withdrawal fidelity. No reliable persona/diplomatic/multi-agent gain, independent review or strong OOD result.

Latest training remains [18 October](docs/SCENARIO_ROLE_CHECKPOINT_20261018.md): authentic four-speech/128-update Qwen3.5-4B fit, four exact fitting speeches but failed Ukraine transfer/worse NLL. Do not scale this branch or start atomic tokens. Cumulative Qwen3.5 updates remain 4,062; scenario branch128; preserve earlier paired-Brazil256 and separate Qwen2.5 reference582. All four October19 owned GPU workers exited normally; unfamiliar processes untouched. All new bounded source/data/output/review evidence is in Git, no new adapter/archive needed.

The current bottleneck is lossless realization of correctly extracted actor/recipient/time/authority facts. Next candidate: a fresh native-chat writer on a few complete contrasting country targets from other episodes, with a different source episode and strong base-plus-map control frozen before fitting. Current Ukraine cases are exposed development; no forward-time/OOD claim, no new pack/fit/queue. Original October18 failures and preparation remain preserved.

The four-answer explicit seed-only control prepared on 7 October remains unrun and is not a prerequisite. Do not launch automatically. Recheck live GPU ownership before any operation; old occupation observations do not establish availability. Runners require zero memory/utilisation/no resident process. Preserve all original data, reviews/failures, Germany/China work and private releases. Same-assistant authorship/grading and semantic ambiguities remain explicit; a software replay never clears independent review.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
