# Matched chosen-only SFT, 6 October 2026

Removing the new preference gradient **retains all exact fitting successes but does not fix transfer**. Chosen-only SFT reproduces the same 267-word answers and the 276-word full-repair answer, with 24/24 source units and the original source/synthesis checks. On the unfitted mixed revision, its national facts improve but its recommendation explicitly restores evidence before care. Mali still lacks important facts, and one answer degenerates into repeated “further alignment.” There is no task-quality win to scale from this objective change alone.

This checkpoint adds **96 optimizer updates and seven complete public outputs**, all read and uncapped. Twenty-one previous actual control/comparison outputs were reread; none is counted as new. Cumulative Aurora Qwen3.5 updates become **702**. Both objective branches separately have **256 parent +96 new =352**; they are siblings, not a 448-step sequential branch. Qwen2.5 reference training remains **582** and Germany/China work is preserved.

## One changed objective

Use the exact preceding three pairs, source spans, audited card/ten repairs, targets, negatives, native tokens/masks and seven complete requests. Continue the same saved 256-step adapter with a fresh optimizer; keep 96 updates, 32 presentations per pair, learning rate 5e-5, batch/accumulation one, seed42, disabled dropout, pinned Qwen3.5-4B/runtime, and **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Greedy nonthinking generation remains capped at 2,048 tokens with an 8,192 combined-length guard. No target, source, criterion or instruction repair is made for this comparison.

The pinned TRL trainer's native `sft` term is mean cross-entropy over chosen completion tokens. Its real configured loss equals the separately measured chosen NLL on each pair; DPO is absent from the optimized sum. Actual gradients with respect to model logits confirm zero gradient on rejected rows, prompt/padding positions and the final unused prediction, with nonzero chosen completion gradients on all three real pairs. These checks do not accumulate parameter gradients or make updates. Cached parent reference and negative forward compute remain for matching paired preprocessing/batching; this is an objective ablation, not a streamlined SFT implementation. Reference-relative reward metrics remain diagnostics and are not optimized here.

The starting adapter already contains historical SFT and DPO+NLL updates. This tests **removing DPO in this continuation**, not training an entirely SFT-only pipeline from the base model. Same native dataset order and configured seeded sampler are retained; the old combined run did not record a separate per-step pair-ID sequence, so configured order/seed and observed presentations are the evidence, not a newly claimed historical sequence log.

All four full national speeches, full card and edits, three complete chosen/rejected texts, seven entire system/user/assistant requests, every frozen criterion, fourteen base/parent controls and seven combined-loss outputs were reread. Repeated source/card bytes were checked against the complete displayed text. Seven new outputs were then read in full before selecting another experiment. Same unblinded assistant writes/audits/grades; independent review remains pending.

## Failed guard and actual fit

The first attempt's full-logit gradient check ran before activation checkpointing, in evaluation mode, and exhausted GPU memory. It stopped at **zero optimizer updates and zero generated answers** after passing the real component-loss checks. Its code, ownership and failure records remain under `runs/aurora-chosen-sft-fit-20261006-v1`.

The separately bound v2 enables the trainer's identical activation-checkpoint settings and training mode for that guard. Data, objective and training settings are unchanged. All three real gradient checks pass. The fit records **96 microbatches/optimizer steps/finite-gradient checks**, all 496 adapter tensors changed and finite, and 32 presentations of each pair. Processed sequence tokens are **388,032**; both completion masks total **61,056**. Only **33,280 chosen completion tokens** receive the SFT loss. The parent reference digest stays exact; saved default-adapter tensors and perturb/reload logits match.

Training takes **257.34 seconds** with **19.87 GiB** peak allocated memory, versus the combined continuation's 261.50 seconds/29.92 GiB under the paired setup. This observed memory reduction is a useful technical simplification, not model-quality improvement. Clean fitted chosen-NLL is .000082172 and mean-token accuracy1.0. Reference-relative reward accuracy is2/3 versus the combined arm's1.0; neither value measures held task quality.

## Complete-output comparison

Provisional counts use unchanged frozen units. Unratable judgments remain separate. A higher source count can coexist with a harmful application.

| Task | Base | Starting256 | DPO+NLL352 | Chosen-SFT352 |
|---|---|---|---|---|
| Audited-card exact |21/24|24/24|24/24|24/24, verbatim|
| Raw WPS exact |22/24|24/24|24/24|24/24, verbatim|
| Card own-wording request |21 met +1 unratable/24|24/24|24/24|24/24, still verbatim|
| Full legitimate repair |16 met +1 unratable/24|16 met +2 unratable/24|24/24|24/24, verbatim|
| Mixed partial repair |17 met +2 unratable/24|16 met +3 unratable/24|18 met +1 unratable/24|20/24, application fails|
| Partial application units |3/4|2 met +1 unratable/4|1 met +1 unratable/4|2/4|
| UK Mali pressure |6/14|6/14|4/14|4 met +1 unratable/14|
| UK Mali checked plan |9/14|8/14|5/14|5 met +2 unratable/14|

The new partial memo's source-faithful national-fact prefix eliminates the prior shared pregnancy-choice claim and ambiguous national-rule phrasing. But it recommends **“restoring evidence before care”** with an early-review exemption only for imminent pregnancy loss. That does not remove the remaining access gate for other survivors. It still omits acknowledgement that final conviction is already waived. The improved20/24 source count and2/4 application count are not a successful current-state policy recommendation.

Mali pressure omits the qualified adoption welcome, instability/humanitarian qualification, Wagner, the named UN arrangement, October protection concern, SOFA and continuing-support scope; timeline authority is ambiguous. It gives steps but no practical trade-off or explicit future-vote answer. Repetition makes much of its conclusion incoherent. The checked-plan answer omits other required facts and leaves unspecified national “red lines” and another-delegation objection ambiguous. Its proposed proportionate import checks might impose a barrier, but their effect is unstated; do not call that a definite source-opposed restriction. The earlier combined answer explicitly recommended temporary restrictions and keeps its original failure grade.

## Next decision

Both objectives fit complete examples and both fail mixed-state application/outside-source checks. Removing the new preference gradient is insufficient to solve this bottleneck. Keep both saved branches and the simpler loss as a technical option; do not declare a best country-persona model from these development counts or append canonical full answers indefinitely.

The next candidate is a **bounded application-paragraph diagnostic** across base, starting256 and both352 branches: identical complete sources and current mixed revision, with the faithful national-fact prefix supplied, requesting only the remaining analytical paragraph. It tests whether composing source facts and state-dependent application together interferes with delivering the application. Compare with the already inspected full-memo outputs. Success would motivate a structured composition trial with strong base controls; failure would redirect attention to state/application supervision. A supplied correct prefix is an easier component control, not independent source parsing, full-task transfer or persona success. **No next pack, fit, queue or sweep is prepared.**

Seven new answers use **2,258 generated tokens and55.10 seconds** of measured generation. Both positively recorded process identities exited naturally, with zero terminations and no unfamiliar-process changes. Frozen bytes, actual launch/code/token/weight provenance, matching parent/inputs/runtime/GPU/budget, masks, chosen-only loss/gradients, reference, exposure, saved weights and stored annotation arithmetic pass portable verification. No fresh software-test count, sealed OOD, native-vote or autonomous multi-agent gain is claimed.

Evidence: [preparation](../reports/chosen-sft-preparation-20261006.json), [guard correction](../reports/chosen-sft-preparation-20261006-v2.json), [measured checkpoint and ownership](../reports/chosen-sft-checkpoint-20261006.json), [portable verification](../reports/chosen-sft-20261006-v2.json). Exact frozen data remain `data/prepared/repaired-state-20261006-v1`; actual/failed/code/weight/complete inspection records are `runs/aurora-chosen-sft-fit-20261006-v1` and `v2`. All previous source/rubric decisions and dated grades remain preserved.
