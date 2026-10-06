# Country source cards and their realization, 6 October 2026

Separating the two national statements into source cards improves some local facts but does not establish faithful composition. The saved adapter can still reverse the UK care claim, assign UK-specific justice language to France, or omit required source facts. Even supplying an explicitly edited, source-audited card does not make either writer pass the original source checks. This checkpoint closes the card/prompt diagnostic before further fitting.

Six new public outputs were read in full, with **zero optimizer updates**. All six finish without reaching the output cap. Cumulative Aurora Qwen3.5 updates remain **414**, the selected adapter branch remains **160**, reference Qwen2.5 remains **582**, and Germany/China remains separate and preserved.

## Sources, controls and complete inspection

The unchanged sources are the complete France/UK post-vote statements in S/PV.8514, 23 April 2019. Both welcome resolution 2467 while criticizing omitted sexual/reproductive-health language and making real continuing-care commitments. France explicitly discusses involuntary pregnancy, termination, bodily autonomy and the reaffirmed 1889/2106 framework. The UK explicitly discusses civil society and remaining justice/accountability work. Welcoming adoption does not endorse every omission; actual continuing support does not guarantee a future text or vote. The present conviction-gate proposal is hypothetical.

Both full statements, every prompt, all 24 original national units, four source guards and five synthesis checks were read. The two-country card prompt explicitly asks for source-specific details, real commitments, unknown future votes and concrete hypothetical application. It also removes the original 300-word memo limit. Thus this intermediate diagnostic changes requested coverage, format and output pressure together; its scores cannot be interpreted as an isolated format effect or an improvement on the original memo task.

Use pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, the unchanged runtime, greedy nonthinking decoding, 2,048 generated-token allowance and 8,192 combined-length guard. Base and the saved rehearsal adapter use identical inputs within each comparison on **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Model, adapter, source spans, runtime/code and actual token IDs replay. Each complete output was inspected before the next launch; no fit or sweep was queued.

## First cards and one inspected instruction repair

| Stage | Base national units | Adapter national units | Strict source pass |
|---|---|---|---|
| Initial cards |20 met +2 unratable/24|19 met +1 unratable/24|Neither|
| Added boundary checks |21 met +2 unratable/24|20/24|Neither|
| Original memo with edited audited card |21/24|19/24|Neither|

Initial base cards preserve many policy details and exact continuing-care quotes, but invent offices for both speakers. Their procedural-acceptance wording is ambiguous. The initial adapter falsely says France's pregnancy/bodily-choice position is absent, despite other correct clauses, and pools the UK civil-society/further-justice assessment into the two-country coda. Its proposed care/accountability steps remain vague; requested exact quotations are absent.

After both outputs were read, one prompt repair asks the model to check bounded roles, absence claims, adoption versus policy endorsement, country-specific common ground and concrete operational recommendations. It adds no new national facts. This is an exposed development repair, not fresh confirmation. The base retains an incorrect inference that UK regret partly supports the colleague's acceptance claim. The adapter repairs the French pregnancy omission and office guesses, but says that UK support “does not accept the acute need” for care, changes recognition of an existing achievement into a condition on further justice, and again pools the UK assessment into France. Correct care clauses elsewhere do not erase a contradictory clause. These cases retain their original annotations and unratable judgments pending independent adjudication.

## Audited card supplied to the original memo task

The actual second adapter card is preserved unmodified alongside a selected card with **ten explicit assistant edits**. The edits repair operator/object polarity, remove the invented recognition condition, keep the justice assessment attributed to the UK, preserve the reaffirmed framework, separate continuing promises from unknown votes, make parallel care/accountability recommendations concrete, and add two literal source quotations. Every edit and the entire 909-word selected card were read against both complete statements and the original criteria. Its 24/24 input audit describes supplied data, not model performance. This is an actual model card plus assistant editing, with no independent teacher API transcript.

Both bridge inputs preserve the original raw memo question/source/system text and append that same edited card. The original 300-word request remains. Longer input, supplied corrected facts and stronger coverage are disclosed; there is no autonomous planner success or isolated schema comparison.

The base memo converts hypothetical analytical implications into claims that France explicitly rejected care contingent on particular outcomes and that the UK affirmed accountability must not gate care. Those specific assertions are absent from the bounded speeches. It also omits the UK source assessment of further justice/accountability work. Its 358 words exceed the requested limit.

The adapter's 248-word memo correctly distinguishes adoption from accepting omissions and labels its operational recommendation. However, “Each also affirms further justice and accountability steps” pools the bounded UK assessment into France. Both national adoption/welcome facts are omitted, as are France's explicit pregnancy-termination right and the continuing reaffirmed framework: merely citing earlier resolutions does not supply the latter. Generic bodily autonomy plus an analytical pregnancy-choice recommendation does not replace the specific national source statement. Those five units are unmet, giving 19/24. Neither output passes all source guards and synthesis checks.

## Evidence and next decision

Measured generation is **5,691 tokens and 106.7 seconds**, excluding model loading and artifact work. All six recorded model identities exited naturally; no terminations or unfamiliar-process changes. There is no new optimization, independent semantic review, sealed OOD confirmation, native vote forecasting or validated country-persona/multi-agent gain. Original WPS criteria, historical scores, sources, frozen packs, transcripts, adapter weights and failed receipts remain preserved.

Portable verification replays source bytes, actual input/output tokens, matching model/runtime/hardware, loaded adapter hashes, archived inference code, every stored annotation denominator, and all ten edits from the original model card. This is reproducibility of assistant annotations, not independent regrading. Inference implementation is unchanged; the preceding seven parser/presence guards remain the relevant software evidence, and this checkpoint adds no model-quality test claim from software checks.

Evidence: `reports/country-source-cards-checkpoint-20261006.json`, `country-source-cards-20261006-v1.json`, `country-source-cards-20261006-v2.json`, `country-source-bridge-20261006-v1.json`, and `country-source-cards-resource-status-20261006.json`. Frozen inputs/criteria/source proof/card repairs are in the three matching `data/prepared/country-source-*` packs; actual launch/code/token/output/inspection records are under `runs/aurora-country-source-*`.

The next candidate is a minimal source-fidelity preference contrast with a chosen-answer likelihood anchor: source-audit one complete preferred answer against an actual writer error, freeze the exact-prompt, changed-wording, strong-input and separate-family comparisons before optimization, then inspect one small fit before any expansion. This tests a different supervision signal from the full-memo SFT that already memorized episodes without dependable transfer. It must preserve real continuing commitments and useful country differences, rather than reward generic caution or manufactured disagreement. Earlier pure DPO did not improve aggregate Mali coverage, and the published humor recipe also used chosen-NLL, approximate KL and later introspective SFT; this candidate would not be an exact reproduction or an isolated comparison with that historical run. No next pack, fit, queue or sweep is prepared.
