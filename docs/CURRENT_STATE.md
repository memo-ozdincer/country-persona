# Current state — 19 October 2026

Dated reports and complete artifacts are the evidence; this file guides navigation.

Wrap-up source review: [role-contrast design](ROLE_CONTRAST_DESIGN_20261019.md) verifies two complete climate statements/eight source spans and defines a country-role contrast with a legitimate-agreement control, without a supplied decision rule. Design only: zero new answers/updates, no executable pack or queued run. Latest measured results below are unchanged.

Wrap-up infrastructure: [CPU CI repair](CI_REPAIR_20261019.md) records the reported workflow failure, missing dependencies/runtime-profile fixes and 242 passing Git-only software tests (23 private-artifact skips). No additional production generations or optimizer updates. User requested wrapping up; no experiment is queued.

## Latest measured checkpoint

[Scope/partial-state training and composition](NATIVE_SCOPE_PARTIAL_CHECKPOINT_20261019.md): one fresh **48-update Qwen3.5-4B** fit retains five messages/targets/units byte-identically and adds one **81-word** India application-only partial-state target. All **25 generated answers and two composed documents** hand-read; 5,616 new output tokens. Facts and a conditional action rule are supplied; same assistant curates, authors targets and grades. Independent review remains pending.

All six fitting contracts pass53/53 material/36guards, five exact target strings. WPS source retains18/18,2/2 strict. Brazil source now9/9 at166words versus native40 8met/1uncertain. Application-only scope improves0/3→3/3, but source/fiction ownership and action/authority ambiguities prevent full passes. Full WPS application retains24/24 material+18/18 map, still1/2 strict: UK196words passes, France257words fails240cap. Original full Brazil regresses to8met/3unmet/2uncertain at202words versus native40 10met/1unmet/2uncertain. Native48 is not a general upgrade.

A separate typed composition uses the exact166-word model source for both arms, with a74-word companion budget and explicit ownership cues. Base55-word component yields221 total,10met/1unmet/2uncertain of13. Native48's67-word component yields **233 words,13/13 material and6/6 source/length guards**. It omits the requested literal Authority heading; the full label-format contract still fails. No text edits, truncation or extra writer call. This is one adaptive, fully specified same-source prototype, not a repair of the original ambiguous direct task or a sealedOOD/persona/collective result.

All48 input/mask/finite-gradient/exposure traces and actual generation/review records replay;114,488 sequence/9,072 supervised tokens. All496 adapter tensors change, base versions unchanged, same-base perturb/reload probe exact, cold saved tensors and a separate cold-model adapter load match. Six owned GPU workers exited normally; unfamiliar processes untouched. [Training replay](../reports/native-scope-partial-replay-20261019-v1.json), [composition replay](../reports/native-typed-composition-replay-20261019-v1.json).

## Next decision

Test one role-only contrast grounded in genuinely differing dated national positions, **without a supplied action rule**. This distinguishes format compliance from source-based policy application. No next pack, fit or sweep is prepared. The broad research goal remains active: dependable national persona, diplomatic reasoning, multi-agent and strongOOD gains remain unproved.

Cumulative Qwen3.5 updates **4182**, current fresh branch48. Preserve [native40](NATIVE_APPLICATION_WRITER_CHECKPOINT_20261019.md), [native32](NATIVE_PLAN_WRITER_CHECKPOINT_20261019.md), [grounded-role decomposition](GROUNDED_ROLE_CHECKPOINT_20261019.md), raw-speech128, paired-Brazil256 and separate Qwen2.5 reference582, all original reviews/failures and Germany/China. Do not scale raw-speech SFT or launch atomic tokens. The [7October explicit seed-only control](EXPLICIT_SEED_PREPARATION_20261007.md) remains preserved/unrun, not a prerequisite.

## Storage and synchronization

All bounded packs, readable examples, outputs, reviews and runtime metadata have exact Git mirrors; saved adapter/config/manifest use a separate private delivery. [Restore manifest](../reports/native-scope-partial-adapter-manifest-20261019-v1.json) records metadata pairs and dependencies. Credentials/base weights/caches/runtime remain external. Immutablev47 and prior releases remain preserved; no new whole archive. Use the pinned overlay verifier in START_HERE.md and the separate new-run inventory. Follow [storage policy](STORAGE_POLICY.md) and [handoff operations](HANDOFF_OPERATIONS.md). Old GPU observations never establish current availability.
