# One complete synthesis target, 6 October 2026

One source-audited complete answer is now learned verbatim and reproduced from saved weights. That establishes a working fitting result. It does **not** establish reliable synthesis on another event. The remaining transfer failures concern speaker/object attribution, polarity, qualifications and unsupported inferences, rather than inability to optimize this target.

This checkpoint adds **32 actual optimizer updates and 20 complete generated answers**, all read: six base controls, six saved-parent controls, six post-fit answers and two cold saved-state checks. CPU replays generated no answers and performed no optimization. The first GPU fit stopped before optimization; its inputs, error, archived code and console remain.

## Data, initialization and controls

The parent is the preserved four-target, fresh 64-step Qwen3.5-4B adapter. Add one 235-word complete climate/security memo, using the full S/PV.8923 speeches and original national questions. Private teacher bullet plans are absent from its training input. The target covers all 24 original national units, separates UK draft support from unknown quota approval, explicitly limits documented G-5 support to France/India, and marks proposals as analytical options.

All four complete climate speeches, four complete Ukraine speeches, both sanctions statements, questions, atomic criteria, actual peer notes, the target and checked Ukraine plan were read before fitting. Primary PDF hashes and whole national spans replay against the original column-normalized documents. This is not a fresh Poppler extraction. Targets and plans are assistant annotations, without an independent teacher API transcript.

Six matching inputs test the exact training task, original frozen-peer climate context, raw Ukraine synthesis, Ukraine with a strong checked plan, and original India/Brazil sanctions controls. Ukraine is outside the parent/new adapter's fitting data, but historically exposed to the researcher. Climate is now a training event; peer-context results are within-event transfer. The original peer notes are unchanged and were not regenerated with the new weights. This is not a new autonomous full-deliberation run or sealed confirmation.

All arms use the pinned native Qwen3.5-4B, greedy inference with thinking disabled, 512 output tokens and 8192 context. Hardware remains **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Every complete prompt fits without truncation and every output ends below its cap.

## Guarded correction and measured optimization

The v1 row omitted explicit per-row `enable_thinking=False`. TRL's native training template and the independently audited tokenizer sequence differed. The actual trainer-mask guard raised before `trainer.train()`. No optimizer update occurred.

Versioned v2 restores that row metadata, matching the working four-target data. Target text, full sources, six evaluation prompts and semantic criteria are byte-identical to v1. The installed trainer preprocessing and collator reproduce the old error and pass the corrected mask on CPU. Actual base/parent generation tokens were rerendered against v2, copied into explicitly labelled replay artifacts and linked by original-run hashes. No fictitious GPU launch or new control model call was created.

The new optimizer continues the saved parent tensors, not an optimizer-state resume. The initial tensor digest matches the saved parent. Actual training processes 145,888 sequence tokens and 11,136 supervised tokens: 32 presentations of one 4,559-token sequence, 348 tokens supervised per presentation. Although accumulation is configured as 2, the one-row epoch flushes its partial batch; it does not produce 64 microbatches. The counter-based replay preserves this distinction.

Target loss falls 2.3488→0.001704. All 496 adapter tensors change; 32 finite-gradient checks pass. Training takes about 155 seconds and peaks at 11.66 GiB. Exact saved tensors and perturbed-state reload pass. The selected new branch has 64 parent plus 32 new updates; cumulative recorded Aurora Qwen3.5 updates are 318, including the older lost 20-step DPO fit. Reference Qwen2.5's 582 and historical Germany/China remain separate.

## Actual free-generation results

| Input | Base required units | Parent required units | New fit required units | New-fit source result |
|---|---:|---:|---:|---|
| Climate exact training task |12/24|13/24|24/24|Exact target; all 4 source guards and 5 synthesis checks met |
| Climate frozen peer context |14/24|14/24|24/24|Ambiguous coda, source/synthesis checks unratable; no strict pass |
| Ukraine raw |19/25|14/25|17 met +1 unratable /25|UK polarity and speaker/date errors survive; no strict pass |
| Ukraine checked plan |19/25|21/25|23/25|Two omissions and unsupported recognition condition; no strict pass |
| India sanctions retention |4/5|5/5|4/5|Proactive qualifier omitted |
| Brazil sanctions retention |3/5|5/5|5/5|Additional unsupported legal-only claim; content count does not certify source fidelity |

The exact answer matches the 235-word target verbatim. It covers the omitted UK women/girls participation and Indian developing-country participation, retains the other units and avoids false consensus, writing dates and amounts. This is learned realization on a fitting input, not evidence of general persona change.

The peer memo retains the content but changes explicit G-5 support into “these positions” after all four national paragraphs. Whether that refers to regional-force support or the whole preceding position set is unresolved. The UK draft-versus-quota distinction does not itself assert approval or rejection; no keyword is required for that semantic boundary. Prior ambiguous grades remain preserved.

Raw Ukraine corrects the UK draft position in its body but calls it opposition in the conclusion; the correct clause does not erase the incompatible one. It also moves the draft-support statement to the Foreign Secretary “last week”, whereas the current source is Kariuki at this meeting. Some assistance/cost details disappear. Brazilian “then-current” conditions/assessment become ambiguously undetermined despite an earlier negative assessment.

With the strong plan, required content increases but the model omits France's support duration and India's legal-order principle, then adds an unsupported French recognition requirement. India's original sanctions response loses the proactive role qualification; Brazil adds “only the Council” has binding authorization, absent from the supplied statements. These whole-response observations are retained alongside required-content scores. None supports a held-family strict improvement.

## Saved-state verification and next decision

A fresh saved-adapter load reproduces **every input/output token** for the exact task and raw Ukraine case. Both full outputs were read. Therefore exact learning and the remaining raw failure survive serialization and a cold context; they are not just trainer-state artifacts.

Keep the original four-target parent, eight-target sanctions branch and this new complete-target branch. Do not repeat fitting on the already learned target. The next natural candidate is a second complete episode that explicitly preserves speaker/date, object/polarity and cross-paragraph consistency, with the original four targets rehearsed to preserve their details. Freeze a third source family and strong checked-plan control before fitting; match the successful per-target exposure rather than undertraining a larger set. A structured source-ledger comparison remains an alternative if prose diversity does not repair attribution. No new target mix, fit, queue or sweep is prepared.

These are one unblinded assistant's exposed-development annotations. Independent semantic review and adjudication remain pending. There is no native action-prediction, private-value, autonomous multi-agent or validated country-persona gain. Twenty existing required-content points do not automatically defeat an unsupported extra claim.

Measured and portable replay: `reports/minimal-synthesis-fit-20261006.json`, `scripts/verify_minimal_synthesis_fit.py`. Native template repair: `reports/minimal-synthesis-template-repair-20261006.json`. Cold generation: `reports/minimal-synthesis-cold-20261006.json`. Nineteen existing training software guards pass. Ownership: `reports/minimal-synthesis-resource-status-20261006.json`; all five actual model identities exited, zero terminations or unfamiliar-process changes. Both frozen preparation versions, original annotations, CPU diagnostics and full actual traces remain in the private handoff.
