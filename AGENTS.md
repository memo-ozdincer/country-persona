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

## Current boundary — 18 October 2026

Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md) for the current measured state, pending control and storage verification. Historical checkpoint summaries remain in `docs/PROJECT_HANDOFF.md`, their dated reports, Git history and the immutable v47 snapshot. They are evidence, not a queue of current instructions.

The four-answer explicit seed-only control prepared on 7 October remains unrun: two base answers, inspect, then two saved-adapter answers and inspect. It adds an explicit no-peer mode to the old common-seed task. Keep sources, H1, starting drafts, rubric, runtime, weights and decoder fixed. Do not launch automatically. Recheck live GPU ownership; old occupation observations do not establish current availability. The runner requires zero memory/utilisation and no resident process.

Latest measured checkpoint: read `docs/SCENARIO_ROLE_CHECKPOINT_20261018.md`. Fourteen generated answers were hand-read and one fresh four-target/128-update Qwen3.5-4B fit completed. All four authentic UK/India sanctions/climate fitting speeches reproduce exactly, all 20 fitting units/guards pass; both Ukraine development cases fail under raw and corrected-native adapter prompts. Source NLL worsens in both matched formats, with invented policies/events and an extra US turn. Do not scale this branch or launch the atomic-token arm. Independent review and persona/diplomatic/multi-agent/strong OOD gains remain unproved.

All 128 input/mask/gradient/exposure traces replay; base parameter versions remain unchanged, saved/reloaded probe logits match, and a separate cold 4B adapter load matches the trained tensor digest. Cumulative Qwen3.5 updates 4,062; new branch 128; preserve the prior paired-Brazil branch 256 and separate Qwen2.5 reference 582. All five owned GPU workers exited; an unfamiliar process briefly joined the training device and left naturally, never altered. No next run is queued.

The native wrapper's embedded record-end tokens were repaired in a separately preserved control. Exact reconstruction of some held criteria requires historical facts absent from the provided windows; omissions alone do not establish poor persona beliefs. Sources have historical exposure, and sanctions fitting is later than the Ukraine development episode: no forward-time or sealed OOD claim. The next candidate is native-chat evaluation with fully grounded pre-target meeting/country evidence and identifiable role/topic controls before more optimization. No next pack or fit is prepared; the old explicit seed-only control remains preserved/unrun and is not a prerequisite. Preserve all original data, reviews/failures, Germany/China work and private releases.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
