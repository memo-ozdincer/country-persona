# Source-audited preference comparison — 3 October 2026

A fresh twenty-step Qwen3.5-4B pure DPO fit learns the supplied preference contrasts but does not establish an aggregate fidelity gain over base. Every complete answer was inspected. This follows the inspected [matched clause-weighted comparison](AURORA_COVERAGE_OBJECTIVE_20261003.md), which reduced coverage. Together these checkpoints add 22 complete answers and 60 actual optimizer steps: two useful twenty-step fits and one twenty-step DPO technical attempt lost before saving.

[Measured receipt](../reports/qwen35-source-preference-20261003.json), [portable verification](../reports/qwen35-source-preference-verification-20261003.json), [frozen pair decision](../data/prepared/source-preference-20261003-v1/decision.json).

| Same four raw Mali cases | Met | Unmet | Unratable | Strict passes |
|---|---:|---:|---:|---:|
| Base | 35 / 52 | 17 | 0 | 0 / 4 |
| Saved uniform SFT | 31 / 52 | 21 | 0 | 0 / 4 |
| Clause-weighted SFT | 30 / 52 | 22 | 0 | 0 / 4 |
| Source-preference DPO | 35 / 52 | 14 | 3 | 0 / 4 |

On 49 jointly ratable units DPO makes six corrections and three regressions versus base, nine/two versus uniform, and eleven/three versus weighted. Three Brazilian dialogue/durable-peace compound meanings need adjudication and are never counted as met. Earlier stored ratings and frozen criteria are preserved, not rewritten to favor a selected arm. Same unblinded assistant authored pairs/criteria/source checks and grades; these are dependent development annotations, not independent estimates. Units and repeated turns are not independent samples.

Historical exact sanctions controls score base 18/24, uniform 16/24, weighted 17/24 and DPO 17/24; zero strict passes. DPO restores Brazil's operational amendment and food/inflation costs, but loses India's distinct reporting demand and adds unsupported 10 December writing dates to both answers. Indian timely aid is retained without a universal pre-delivery gate; new future-support conditions remain invented. Missing requirements are already in the preferred targets.

## Intervention and relation to the paper

The twenty original student inputs and preferred targets remain byte-for-byte unchanged. Each rejected answer contains one inspected edit: a reversed vote/position, pooled speaker claim, invented guarantee/condition, harmful universal gate, or omitted qualification. Rejected lengths differ by only −4 to +2 tokens per row; totals are 4,710 preferred versus 4,697 rejected tokens. Specificity/application preferences are assistant judgments, not all verbatim observed national decisions. In particular, the human-rights/law edit is an omission contrast, not an entirely contradictory answer. Independent pair/source review remains pending. No preference is assigned merely because an answer came from a teacher or sounds more assertive.

Pure sigmoid DPO, beta 0.1, fresh rank-8 all-linear LoRA, learning rate 5e-5, batch one with two accumulated microbatches, twenty steps, seed 42 and 0.05 LoRA dropout. The reference is the exact base with the adapter disabled; its scores are cached before optimization. There is no extra chosen NLL, per-token KL penalty or introspection stage. Student inputs contain no private teacher plan. Extra rejected supervision and reference computation mean this is not an equal-information/equal-compute objective-only comparison with SFT.

[Open Character Training, §2.3](https://arxiv.org/html/2511.01689v1) motivates using preference contrasts, but its pipeline also adds chosen-generation NLL and per-token KL, then synthetic introspective SFT. This tiny institutional-source experiment is not a reproduction of that pipeline or evidence about national private values. We retain the country–institution–role–date boundary and separate official commitments from analyst recommendations.

Mali S/PV.9365 was separately frozen before the coverage baseline and lies outside fitted sanctions/climate families. DPO was selected after inspecting those Mali answers, so its reuse is exposed development. Fixed assistant-authored peer histories test unsupported consensus and a genuinely improved proposal; they are not autonomous interactions. Topic and history format shift together, preventing attribution of transfer failures solely to topic. Unknown public-record pretraining exposure prevents a certified broad-OOD claim. None of these supplied-outcome tasks measures native vote prediction.

## What the outputs teach us

The fitted-pair reference-relative reward accuracy reaches 1.0 and mean margin 1.080. These are diagnostics on the same twenty fitted pairs, not a benchmark. Preferred log-probabilities also improve relative to the reference; the result is not evidence that preferred likelihood collapsed. Pairwise success does not require a complete faithful greedy answer.

DPO improves some implementation steps and practical trade-offs, especially when the hypothetical proposal changes. But Brazil's hoped-for renewal/positive MINUSMA assessment remains absent, UK Wagner/SOFA/election qualifications disappear, UK positions pool into Brazil's briefing, and a UK direct-funding trade-off is fabricated. A correct unknown-vote disclaimer coexists with invented official conditions. Both pressure resistance and legitimate revision must be evaluated; rewarding disagreement would not solve these source/attribution errors.

All twenty gradients are finite, all 496 adapter tensors change, and state perturb/reload plus same-base probe logits match exactly. The fit processes 159,086 sequence and 18,814 target tokens; frozen-reference setup adds a paired forward pass. One NVIDIA RTX PRO 6000 Blackwell Server Edition; training 104.25 seconds, peak allocated 24.92 GiB. Generation uses the same source helper, model bytes, runtime, greedy/thinking-disabled protocol and frozen input tokens as the comparison arms.

## Failures, accounting and next decision

The first preference attempt fails before optimization: TRL's optional Triton backend needs unavailable Python development headers. The second completes twenty steps but diagnostic evaluation duplicates cached reference columns before saving. Both full failure/source records remain. The third uses pinned TRL's built-in FP32 PyTorch fallback, saves/verifies first, and evaluates the already prepared cached-reference dataset through the supported no-argument path. Five focused preference guards include fallback score/mask gradients and this duplicate-precomputation regression. Reference scores are identical across the completed failed fit and retry; stochastic training traces differ, so do not claim an exact recovered adapter. No failed attempt generated quality answers and none was selected by a better behavioral score.

Recorded Aurora Qwen3.5 steps are **142**: two-step smoke plus seven fresh twenty-step fits, including the lost DPO attempt, excluding historical Germany/China training. All project PIDs exited; unfamiliar processes untouched. Five coverage guards, five preference guards, eight existing source/application guards and portable pairing/masks/source/serialization/steps/stored-review replay pass. Software replay does not independently regrade semantics. NCCL and independent source/rubric/semantic review remain pending; no persona, autonomous multi-agent or native-prediction gain is established.

Preserve all arms and adjudicate the three compound meanings. The next training candidate is one matched **DPO + chosen-NLL anchor** using identical pairs and twenty-step budget, with a separately frozen family for confirmation. This isolates the paper's positive-completion term from pure preference comparison. It is a hypothesis about generation fidelity, not a demonstrated cause or optimal coefficient; an improved pair margin alone would not justify it. If that fails, prioritize corrected student histories/explicit source-obligation supervision over another optimization sweep. The [research audit](PERSONA_GOAL_GAP_RESEARCH_20261001.md) supplies conditional trajectory/planner/writer precedents. No next fit, introspective dataset or sweep is prepared or queued.

[All six full answers](../runs/aurora-qwen35-source-preference-20261003-v3/transcript.jsonl), [full inspection with unresolved units](../runs/aurora-qwen35-source-preference-20261003-v3/inspection.json), [ownership/runtime/optimization record](../runs/aurora-qwen35-source-preference-20261003-v3/run.json), [first failed attempt](../runs/aurora-qwen35-source-preference-20261003-v1/failure.json), [completed-but-unsaved attempt](../runs/aurora-qwen35-source-preference-20261003-v2/failure.json).
