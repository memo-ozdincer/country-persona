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

The recursive research goal is **paused at the user's request**. [Consolidated work and results](docs/CONSOLIDATED_RESULTS_20261019.md) reconciles all 4,182 Qwen3.5 updates, the separate 582-update reference and the completed/unrun trial boundary. The current reporting task adds no model work. Historical recommendations and prepared controls are not an automatic run queue.

Read [current state](docs/CURRENT_STATE.md) and [native scope/partial-state checkpoint](docs/NATIVE_SCOPE_PARTIAL_CHECKPOINT_20261019.md). Latest: one fresh 48-update Qwen3.5-4B fit retains five old messages/targets/units and adds one 81-word application-only partial-state target. Twenty-five new answers and two unedited compositions hand-read. Six fitting contracts pass (53 material/36 guards); WPS source18/18 retained and Brazil source9/9 at166words. Application-only scope improves0/3→3/3, but state/provenance ambiguities remain. WPS full application still1/2 strict (France257words). Original full Brazil regresses native40 10met/1unmet/2uncertain→8met/3unmet/2uncertain. Do not call native48 a general upgrade.

A separate typed/common-source composition produces233words,13/13 material and6/6 source/length guards; it misses the requested literal Authority heading, so full label-format contract is not passed. Base221words has10met/1unmet/2uncertain. Same-assistant adaptive case, supplied facts/action rule, no independent/persona/diplomatic/private-value/collective/strongOOD claim. Source is reused once, no hidden writer call or human editing. Preserve all raw outputs, failed contracts, uncertain reviews and preparation errors.

All48 actual masks/gradients/exposure records and outputs replay; base versions unchanged, same-base reload probe exact, cold saved tensors and separate cold-model adapter state exact. CumulativeQwen3.5 updates4182/current48; preserve native40/native32/rawspeech128/pairedBrazil256 and separateQwen2.5reference582. Six owned workers exited normally, unfamiliar processes untouched. Bounded metadata is preserved in Git; adapter delivery is tracked separately by its manifest/receipt. Immutablev47 unchanged.

Next candidate: one role-only contrast on differing dated national positions, with no supplied action rule. No next pack/fit/queue. The7October explicit seed-only control remains preserved/unrun, not a prerequisite; never auto-launch it. Do not scale raw-speech SFT or launch atomic tokens. Preserve Germany/China and all historical releases. Recheck live GPU ownership for any future run; historical observations establish no availability.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
