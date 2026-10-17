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

## Current boundary — 17 October 2026

Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md) for the current measured state, pending control and storage verification. Historical checkpoint summaries remain in `docs/PROJECT_HANDOFF.md`, their dated reports, Git history and the immutable v47 snapshot. They are evidence, not a queue of current instructions.

The four-answer explicit seed-only control prepared on 7 October remains unrun: two base answers, inspect, then two saved-adapter answers and inspect. It adds an explicit no-peer mode to the old common-seed task. Keep sources, H1, starting drafts, rubric, runtime, weights and decoder fixed. Do not launch automatically. Recheck live GPU ownership; old occupation observations do not establish current availability. The runner requires zero memory/utilisation and no resident process.

Last measured checkpoint: twelve-answer India–Brazil sanctions interaction, all twelve strict answers fail; no demonstrated persona or collective benefit. Protocol ambiguity and source/draft attribution errors remain. Same-assistant authorship/grading, historical exposure and independent-review limitations remain explicit. Qwen3.5 cumulative updates 3,934; selected eight-example branch 256; separate Qwen2.5 reference reproduction 582. Preparation and byte verification are not model-quality results.

The latest request is to set up and validate scenario-conditioned chronological country/delegation SFT. Read `docs/SCENARIO_ROLE_SFT_READINESS_20261017.md` and the earlier design. Four complete UK/India sanctions/climate fitting speeches and two fit-excluded Ukraine development speeches are source-audited; every selected body and scenario anchor is mapped, all used text hand-read, and normalization/column coverage replayed. Thirty-five software/runtime checks pass; the final random tiny hybrid-Qwen CPU trace has eight inspected/replayed optimizer steps and exact cold adapter reload. This is engineering evidence, not a production 4B training or persona result. Zero new production answers/updates; counters unchanged.

A frozen readable-marker rank-8 128-update fit config and separate-operation runner now exist, not a launch queue. Next: on a freshly verified free GPU, run/inspect the two base Ukraine sequence replies; use the matched native-chat base control before interpreting serializer failure. If inspection warrants fitting, run only the four-target fit, inspect its trace/fitting recall and held-episode replies, then decide. Atomic-token training remains deferred. The earlier explicit seed-only control remains preserved/unrun and is not a prerequisite for this direction. Preserve all existing experiments, original grades/failures, Germany/China work and private releases.

## Storage and synchronization

Follow `docs/STORAGE_POLICY.md` and `docs/HANDOFF_OPERATIONS.md`. Code/documentation-only updates can be a committed Git overlay over the pinned v47 snapshot; do not create another multi-GB full archive for them. Unchanged ignored evidence must still match the original manifest. Never rewrite a manifest to hide unexplained mismatches. Use the overlay verifier with the independently pinned manifest digest after committing; the original verifier remains for the immutable snapshot.

Treat hardlinked historical staging trees as immutable. Before changing a workspace file, ensure it is not sharing an inode with a snapshot. Keep one necessary delivery representation; remove a redundant whole archive only after exact local part/reassembly verification and remote asset checks, with a cleanup receipt and restore instructions. Do not automatically purge historical snapshots, model weights, datasets, adapters or releases.
