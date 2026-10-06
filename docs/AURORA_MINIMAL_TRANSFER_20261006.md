# Minimum SFT transfer and four-country initial responses

Comparison started 5 October UTC and continued 6 October. The user requests recursive progress from the smallest working country-model element, with all selected data and outputs read before each next step. This checkpoint tests the two preserved 64-step Qwen3.5-4B adapters from [the minimum country experiment](AURORA_MINIMAL_COUNTRY_20261005.md) outside their sanctions training event. It adds **26 complete model answers and zero optimizer updates**.

## What changed and what stayed controlled

The adapters were freshly fitted on four or eight short responses using India/Brazil statements from the 9 December 2022 humanitarian-sanctions meeting, S/PV.9214. The transfer test keeps those countries and uses their complete 9 December 2021 climate/security speeches, S/PV.8923. This family is outside these particular adapters' training, but historically exposed elsewhere in the project. It is development transfer, not sealed OOD confirmation or native vote prediction.

All model arms retain the exact Qwen3.5-4B revision, pinned runtime, BF16 SDPA inference, greedy decoding, thinking disabled and 384-token cap on **NVIDIA RTX PRO 6000 Blackwell Server Edition**. The six-task transfer pack uses the previous 4,096-token context. The subsequent original four-country source packet needs the original protocol's separately recorded 8,192-token context; every before/after input token matches within that comparison. No source or note is truncated.

## Source and case inspection before calls

The assistant read both entire India/Brazil speeches, six complete tasks, two checked plans and every source-specific criterion. Their source positions are different from a generic climate-security consensus: both defend the inclusive UNFCCC process; India supports adequately resourced G-5 Sahel security initiatives and states actual future climate targets; Brazil stresses developed-country financing, non-security root causes, human rights and humanitarian law. Neither speech establishes a future Council vote, and Brazilian silence about the G-5 is not rejection.

The source PDF retains its original hash. Both complete spans and the full normalized-column digest match archived evidence. An initial comparison against the raw, tagged columns text failed because it used the wrong representation; inspecting the original extractor resolved that comparison. An optional fresh Poppler extraction could not run because `pdfinfo` is absent on Aurora. We claim verified archived extraction and PDF bytes, not a new extraction. Source review remains one assistant's inspection.

Prepared v1 was preserved before any model call: its peer claim used “expansion,” which was stronger than India's recorded force endorsement, and its criterion said “nonexistent” rather than source-unestablished Brazilian support. These were corrected and reread in frozen v2. No result was observed under v1. [Complete pre-call inspection](../data/prepared/minimal-country-transfer-20261005-v2/manual-inspection.json) records the bounded absence and genuine-commitment distinctions.

The four raw tasks cover an unsupported joint causal/forum/force statement and constructive venue-respecting cooperation, for each country. India must retain its stated GDP-emissions-intensity reduction of 45% by 2030 from 2005 and net zero by 2070: cautious training must not erase real announced commitments. Brazil must preserve financing/root-cause/legal priorities without borrowing India's specific force endorsement. Two identical-task checked-plan controls remain strong alternatives to fitting.

## Outside-training-family result

| Frozen comparison | Base | Four-target, 64-step fit | Eight-target, 64-step fit |
| --- | ---: | ---: | ---: |
| Four raw responses, five units each | 12/20 | 20/20 | 17/20 |
| Raw application/commitment units | 5/8 | 8/8 | 7/8 |
| Two checked-plan controls | 10/10 | 10/10 | 9/10 |

All eighteen complete answers were read before selecting the next step. The base falsely shares India's G-5 endorsement with Brazil; another answer converts missing Brazilian force evidence into supposed differing forum positions. The four-target fit preserves the countries' actual distinctions, climate-impact nuances and India's real future climate commitments. No old sanctions, carveout or 1267 fact intrudes into any selected adapter answer.

The eight-target branch retains more source discipline than the base but omits India's positive climate-impact acknowledgement, its force-resource problem and the explicit Brazilian non-endorsement distinction in one pressure answer. Its checked-plan Brazil answer also drops the developed-country scaling/timing detail. An Indian international-law claim is borrowed from Brazil's speech. We retain this observation separately from the frozen unit arithmetic. Larger data is not uniformly better: the eight-target branch had better sanctions coverage, while the four-target branch has better coverage here.

[Transfer receipt](../reports/minimal-country-transfer-20261005.json) replays all eighteen actual input/output token sequences, archived runner hashes, pre-call data inspection bindings, saved adapter hashes, runtime/hardware equality and stored annotations. This verifies recorded evidence and arithmetic, not independent semantics.

## Larger step: original questions, all four country roles

After inspecting that transfer, we selected the preserved four-target adapter for a matched check of the **original** four-country climate questions from the existing deliberation protocol. The assistant read the full France and UK speeches, all original questions, all atomic criteria/support anchors and universal checks before calls. All four complete statement spans match the pinned normalized record. The task requires France's Council role and non-military measures; UK reporting, women/girls participation, real draft support and quota uncertainty; India's forum/inclusion/causal qualification; and Brazil's venue/harms/finance priorities.

France and the UK were absent from this adapter's fitting labels. Each analyst sees the same full four-source packet. No peer note, revised output or gold worked answer enters these initial prompts. The original national prompt and 384-token cap are retained. The full source packet fits 8,192 tokens without truncation. This is an initial-response transfer comparison, not yet a trained interaction result.

| Country / original source units | Base | Four-target fit |
| --- | ---: | ---: |
| France | 4/5 | 5/5 |
| UK | 4/5 | 4/5 |
| India | 6/7 | 6/7 |
| Brazil | 5/7 | 7/7 |
| Total source coverage | 19/24 | 22/24 |
| Universal source/attribution/time/commitment checks | 14/16 | 16/16 |

The fit restores France's explicit need to understand reinforcing climate/crisis links and Brazil's financing direction/timing. It avoids the base's unsupported classification of all COP26 commitments as voluntary NDCs. Both arms retain UK draft support and quota uncertainty, but omit meaningful women/girls participation. Both omit explicit developing-country participation under the original Indian inclusion criterion. Cited source IDs remain navigation aids, not entailment proofs.

All eight complete answers were read; none capped. [Initial-response replay](../reports/minimal-deliberation-initials-20261006.json) rerenders every input/output token and checks matched sources/runtime/hardware/weights. The original proposed rubric and historical H100/Qwen3-8B grades are preserved. These new Aurora/Qwen3.5 comparisons cannot be pooled with the old model's scores.

## Decision, limits and ownership

The useful next step is the original synchronous **own-note versus peer-note revision**, using these exact frozen initial answers. Compare corrections, regressions and retention, then feed each revised-note set to the same **unadapted base aggregator**. This will test whether the observed national-response gains survive interaction and help synthesis. Do not assume stronger initials automatically produce better collective analysis. No next fit or seed sweep is prepared; revision/synthesis stages have not run at this checkpoint.

One assistant selected sources, wrote the new transfer tasks and graded every response. Independent construct/source review remains pending. Government public statements are not private beliefs; hypothetical recommendations are not observed diplomatic choices. No intrinsic persona, sealed event OOD, native forecast accuracy or autonomous multi-agent benefit is established. The next comparison must retain source qualifications and avoid optimizing agreement or disagreement as success.

Five recorded model launches exited with PID/start-tick identities checked; unfamiliar processes were not changed and no termination was performed. [Resource receipt](../reports/minimal-transfer-resource-status-20261006.json). Cumulative recorded Aurora Qwen3.5 updates remain **286**; reference Qwen2.5 remains separately **582**. All previous adapters, failed runs, source uncertainties and Germany/China work remain preserved.
