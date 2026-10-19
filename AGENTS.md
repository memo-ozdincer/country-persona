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

Latest [native application writer](docs/NATIVE_APPLICATION_WRITER_CHECKPOINT_20261019.md): one fresh40-update Qwen3.5-4B fit adds one complete labeled India application target while retaining four source targets. Thirteen new answers hand-read including two inspected common-draft revisions; eight historical comparators replayed without new calls. Four source fitting targets exact; application fitting13met/1uncertain. Source-only WPS retention18/18,2/2 strict. Corrected WPS application24/24 plus18/18 map; UK183words provisionally strict, France243words fails240cap. Brazil first-pass10met/1unmet/2uncertain versus base7met/5unmet/1uncertain, both fail: application improves but equality/source coverage/state ambiguity remain. Two common-draft revisions repair none of those seed failures. Same-assistant development; no independent, sealedOOD, national-persona, diplomatic-reasoning or collective gain.

All40 token/mask/gradient/exposure traces and13 actual outputs replay; base tensor versions unchanged, saved/reloaded probe logits exact, separate cold adapter tensor digest exact. Cumulative Qwen3.5 updates4134, current branch40; native32/rawspeech128/pairedBrazil256/Qwen2.5reference582 preserved. Two owned GPU workers exited normally; unfamiliar processes untouched. Bounded evidence is in Git; adapter/config/manifest separately delivered with remote digests checked. Immutablev47 unchanged. No next pack/fit/queue. Next candidate isolates source-preservation versus plan-state reconstruction with explicit semantic coverage and strong base control; no blind dose increase.

Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md). Preserve original grades, adjudications and failures, Germany/China and old releases. Do not scale raw-speech SFT or launch atomic tokens. The7October explicit seed-only control remains preserved/unrun and is not a prerequisite; never auto-launch it. Recheck live GPU ownership for any future run; historical observations establish no availability.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
