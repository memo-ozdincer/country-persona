# Four short national responses: minimum country-pipeline checkpoint

5 October 2026. The user requested recursive experiments in our country data and Qwen3.5 pipeline: read all selected data, fit the smallest useful element, inspect it, and scale from evidence. This supersedes the previous candidate to port another humor positive control. The successful Open Character reproduction and every previous country result remain preserved.

## Question and frozen task

Does short complete-answer SFT preserve national distinctions, respond to a legitimate repair, and avoid inventing commitments, when the same long-source task previously lost details? Before changing objectives, can the existing pipeline actually fit four faithful responses?

The pack uses the complete India and Brazil national statements from S/PV.9214, 9 December 2022. India recognizes timely humanitarian relief and agency predictability, warns of terrorist exploitation, and sought a proactive 1267 Monitoring Team role with robust reporting; the statement says its specific concerns were **not fully addressed**. Brazil sponsored the initiative and voted for resolution 2664, emphasizes predictable humanitarian operations and civilian protection, and recognizes useful sanctions and legitimate security concerns. Neither statement guarantees a future vote. India's specific mechanism request is not a documented Brazilian red line.

All student inputs include both full statements and an assigned national delegation. Four assistant-authored, source-checked targets cover two roles × unsupported endorsement pressure/legitimate mechanism repair, each in a short complete response. No private plan is included in training. Ten frozen cases cover two exact training controls, six new-wording pressure/repair/universal-shutdown applications on this same exposed event, and two strong checked-plan controls. The options are hypothetical, not historical proposals or native vote predictions.

This is a small source-conditioned policy application task. It does not establish an intrinsic country persona, unfamiliar-event generalization or autonomous multi-agent improvement. We retain useful disagreement and legitimate agreement; neither unconditional resistance nor more disagreement is the objective.

## Complete selected-data reading and source audit

One unblinded assistant read both complete national statements, all four targets and their tasks, all ten evaluation tasks, both checked plans and every frozen criterion. Repeated source text in every input is byte-checked against the already-read full statements. [Manual inspection](../data/prepared/minimal-country-20261005-v1/manual-inspection.json) binds the frozen manifest and records support/absence boundaries per target. This is assistant inspection, not independent human review.

The original acquired primary PDF and all five archived extraction files retain their acquisition hashes. The selected statements equal their original full-record spans after the original extractor's boundary trimming. The first exploratory comparison omitted that trimming and failed on inter-speaker whitespace; the corrected check follows the inspected extraction code. [Source verification](../reports/minimal-country-source-verification-20261005.json) preserves the distinction.

Universal beneficiary screening is not explicitly prohibited by India in this statement. The hypothetical application guard asks for a practical arrangement that preserves timely relief without fabricating an official screening condition. It must not be reported as a historical Indian prohibition.

## Matched pipeline and inspected first fit

The model/runtime remain the pinned Qwen/Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Torch 2.8.0+cu128, Transformers 5.17.0, TRL 1.14.1 and PEFT 0.21.1. Both runs use **NVIDIA RTX PRO 6000 Blackwell Server Edition**, greedy generation, thinking disabled, no truncation, a separately versioned 4,096-token context and 384-token answer cap. LoRA remains rank 8/alpha 16, all-linear, dropout 0.05, AdamW at 5e-5, microbatch one and accumulation two; only completion tokens are supervised.

The first fit attempt was refused before model import because an unfamiliar process acquired the base run's GPU. It was left untouched; the refusal is preserved. A second attempt stopped before optimization because the JSONL reader returned an iterator and Dataset.from_list requires a list. The loader was corrected, the failed run preserved, and all ten baseline answers rerun and read. Every input and output token is identical across the two baseline runs. No failed attempt made optimizer updates.

The first completed fit made **16 actual steps**, exposing the four unchanged rows eight times: 41,928 processed sequence tokens and 3,400 supervised tokens. Its completion masks were checked on actual trainer batches; all 496 adapter tensors changed, all sixteen optimizer gradient checks passed, and saved tensors plus a perturb/reload probe match exactly. Training took 25.38 seconds. Target loss fell 2.896 → 1.678, still far from fitting the complete targets.

All ten complete model answers were read before selecting another run. The first fit repairs three application/commitment checks among the twelve such checks in six unseen-wording cases, including accepting the offered mechanisms. It still omits required source details, changes “not fully addressed” to “not included,” invents future official actions, and retains India's unsupported future-support condition. Overall frozen coverage is base 37/50 versus short-fit 36/50. These are dependent assistant annotations; shorter output and lower loss are not full fidelity.

The five-unit rubric covers humanitarian priority, security qualification, national attribution, scenario application and commitment boundary. Further invented source facts are separately recorded. A conjunction of those five units does not certify the absence of every unsupported statement: the checked-plan base India answer meets them while inventing a favourable historical vote. The original record reports India's abstention. We retain the frozen unit definitions and preserve the additional observation rather than silently revising the rubric after outputs.

[Sixteen-step portable replay](../reports/minimal-country-16step-verification-20261005.json) verifies bytes, source inclusion, wording separation, before/after token pairing, saved optimization evidence and stored-review arithmetic; it does not independently regrade semantics.

## Longer fit: fitting works, transfer still needs coverage

A single fresh **64-step** fit kept the same four targets and all generation/evaluation settings. Only the optimizer budget changed. It processed 167,712 sequence tokens and 13,600 supervised tokens, with 32 exposures of each row. Training took 94.73 seconds at 9.39 GiB peak allocated memory. Target loss reached 0.002649 and both exact controls reproduced their targets verbatim. The same mask, finite-gradient, changed-tensor and perturb/reload checks pass.

| Four-target pack | Base | 16 steps | 64 steps |
| --- | ---: | ---: | ---: |
| Exact prompt coverage | 7/10 | 7/10 | 10/10 |
| Six unseen-wording responses | 21/30 | 22/30 | 24/30 |
| Strong checked-plan controls | 9/10 | 7/10 | 9/10 |
| All frozen units | 37/50 | 36/50 | 43/50 |

This verifies that the existing pipeline can fit this small task; it does not prove that low loss causes generalization. The longer fit still invents Indian sponsorship under new pressure wording and blurs Brazil's response to a false joint claim. All ten outputs were read before the next data change. [64-step portable replay](../reports/minimal-country-64step-verification-20261005.json) preserves the comparison and original grades.

## Small data expansion at the same optimizer budget

We preserved the original four rows byte-for-byte and added four complete source-attribution/shutdown contrasts. The new examples correct conflated sponsorship/votes and mechanism requests, distinguish proposed safeguards from official conditions, and preserve timely relief. Every addition and all fourteen evaluation tasks were printed and read before calls. The complete historical sources are unchanged.

The new pack has four exact controls, four retained pressure/repair cases, four new peer/partial-repair wordings and two unchanged strong plans. Two new exact-control prompts are unseen by the old four-target adapter. Both the base and that saved adapter were evaluated and fully read before fitting eight targets. The previously untrained partial-repair pair is important: the four-target adapter distinguishes the added Team role from still-missing reporting for both countries, while the base pools roles and overlooks the addition.

The fresh eight-target fit retains **64 steps**, the same seed, LoRA, learning rate and generation protocol. It processes 167,360 sequence tokens and 14,080 supervised tokens, versus the four-target fit's 167,712 and 13,600. Each row now appears sixteen times rather than thirty-two. This compares data diversity at nearly matched total token compute; it does not match exposure per row. Training takes 94.19 seconds at 9.39 GiB. Target loss falls 2.965 → 0.329; every actual completion mask and all 64 gradient/update/save checks pass.

| Expanded pack | Base | Saved four-target, 64-step fit | Fresh eight-target, 64-step fit |
| --- | ---: | ---: | ---: |
| Four exact-control prompts | 11/20 | 15/20 | 20/20 |
| Four retained pressure/repair cases | 13/20 | 16/20 | 19/20 |
| Four new peer/partial-repair cases | 10/20 | 18/20 | 19/20 |
| Two strong plans | 9/10 | 9/10 | 10/10 |
| All frozen coverage | 43/70 | 58/70 | 68/70 |

Across the **eight raw cases outside the eight training prompts**, coverage rises **23/40 → 34/40 → 38/40**. Scenario-application plus commitment-boundary units rise **7/16 → 15/16 → 15/16**. The eight-target fit repairs the remaining Brazil joint-statement failure but appears to regress on India's partial repair. Thus equal aggregate application scores conceal a traded correction/regression. Source coverage and behavioral application are reported separately.

The eight-target responses no longer invent Indian sponsorship/favourable voting in the new attribution tests. Remaining observations include attributing diversion/reporting specifics to Brazil, recommending “joining the resolution” rather than responding to joint wording, and ambiguous future-text caution. A good rubric conjunction does not erase those observations or prove full source fidelity. All fourteen outputs were read before the next action. [Expanded portable replay](../reports/minimal-country-extension-verification-20261005.json) covers bytes, saved optimization, matched inputs and stored arithmetic.

## Qualification before another fit

The partial-repair wording grants an **active** Team role, while India's primary source asks for a **proactive** role. The frozen criterion treats the added active role as progress; it does not independently establish that the role fully meets India's requested mandate. The eight-target answer's failure to acknowledge progress remains in its original grade, with this interpretive qualification. We do not replace old scores or declare a data-imbalance cause from that one answer.

An evaluation-only pack states two literal components precisely: proactive mandate fully provided/reporting absent, and robust reporting fully provided/proactive mandate absent. It adds checked-state controls and compares base plus both saved adapters. All four tasks, both notes and amended criteria were read before calls. No new targets are fitted in this pack. **All three models correctly distinguish both literal states**, raw and with checked notes. Frozen total coverage is base 20/20 and both adapters 19/20; each adapter omits the terrorist qualification in one raw answer. The base invents a previous Indian future-vote statement and a Council review commitment. These observations remain separate from the five-unit arithmetic.

Thus this clarification does not show trained reasoning superiority or prove a data-imbalance cause. It does show that the earlier partial answer alone cannot diagnose inability to track a fully specified mechanism state. The active/proactive distinction must remain explicit in future source/rubric review. We preserve the original scores and qualification rather than replacing an exposed test with a convenient score.

## Accounting and current limits

Three actual fresh fits make **144 new Qwen3.5 updates: 16 + 64 + 64**. Cumulative recorded Aurora Qwen3.5 optimization becomes **286**, including the earlier lost fit. Reference Qwen2.5's 582 updates and historical Germany/China work remain separate. The two failed attempts made zero updates. Twenty-three existing software fault-injection/source-plan checks passed; those establish technical checks, not persona quality.

The checkpoint produced **94 new complete model answers**, including the ten-answer baseline rerun after the loader correction. Every answer was read; none capped. CPU-only replay rerenders every actual prompt token sequence and output text using the saved tokenizer, rehashes archived launch code and weights, and reproduces every stored annotation denominator. Independent saved-adapter inference uses the exact fitted weight hashes. [Measured/full replay receipt](../reports/minimal-country-checkpoint-20261005.json) records all arms; [resource status](../reports/minimal-country-resource-status-20261005.json) checks original PID/start-tick identities for all eleven recorded launches. All have exited; unfamiliar processes were not changed. No termination or account-wide cleanup occurred.

The observed direction is promising enough to test outside these adapters' training event. It still rests on two roles in one historical event, hypothetical applications, reused exposed development questions, assistant-authored targets and one unblinded assistant grader. There is no independent review, sealed OOD confirmation, native action-prediction gain or trained autonomous multi-agent result. Preserve both saved 64-step adapters because the smaller data arm can retain a behavior lost after expansion. Do not select a method from aggregate coverage alone.

**Next decision:** freeze a separately dated policy family outside these adapters' training, compare the same base and both saved adapters on identical complete sources, and retain strong checked-plan controls. A historically exposed project family can diagnose transfer but must not be called sealed confirmation. Inspect that result before choosing broader country data, longer responses or interaction training. No next fit, pack, queue or sweep is prepared. The immediate lesson is to establish actual fitting, then vary data from observed failures, while guarding against changed semantics and new invented claims. It does not isolate why earlier long-task trials failed or show that a novel objective is unnecessary for the full project.
