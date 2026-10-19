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

Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md) and [docs/NATIVE_PLAN_WRITER_CHECKPOINT_20261019.md](docs/NATIVE_PLAN_WRITER_CHECKPOINT_20261019.md). Latest native writer checkpoint:14 generated statements, one fresh32-update Qwen3.5-4B fit. Four checked-map source targets across sanctions/climate all pass35 material units/guards (one exact string). Fit-excluded WPS source statements improve14/18→18/18 and0/2→2/2 provisional strict passes; France outside the four new targets. Same-assistant review, historically exposed source, no independent/sealedOOD/forward-time or national-persona/collective claim.

Harder WPS application remains incomplete. An original no-analysis/recommendation conflict is preserved and separately corrected. Explicit permission restores base guidance; corrected base23/24 met+1 uncertain, adapter21/24 met. Complete-map coverage16met+1unmet+1uncertain→17met+1unmet. Base271/266words, adapter186/170. Both arms0/2 full strict: adapter France omits application and UK omits practical cost. Do not call this a general upgrade or increase dose blindly. Next data candidate: one complete explicitly labeled application example on a fitting-family source while retaining four source targets, with a fresh source-family/country control frozen before another fit. No next pack/fit/queue.

All32 actual input/mask/gradient/exposure traces and14 actual output-token/review records replay, with reused baseline counted once. All496 adapter tensors change, frozen base versions unchanged, same-base perturbed reload probe exact and separate cold adapter tensor state exact. Cumulative Qwen3.5 updates4094; native branch32; preserve older raw-speech128/paired-Brazil256 and separate Qwen2.5 reference582. Three owned GPU workers exited (first after inspection-gate error,two normally), unfamiliar processes untouched. Original error/failed preflights preserved. Bounded metadata is in Git; the new65MB adapter requires its separate verified private delivery. Base weights/credentials excluded; immutablev47 unchanged.

Earlier [grounded-role evaluation](docs/GROUNDED_ROLE_CHECKPOINT_20261019.md) and [raw-speech fit](docs/SCENARIO_ROLE_CHECKPOINT_20261018.md) remain evidence with original failures. Do not scale the raw-speech branch or start atomic tokens. The four-answer explicit seed-only control from7October remains preserved/unrun, not a prerequisite; do not auto-launch. Recheck live GPU ownership; historical availability never licenses allocation. Every run requires zero memory/utilisation/no resident process. Preserve all data/reviews/failures, Germany/China and private releases. Software replay never clears independent semantic review.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
