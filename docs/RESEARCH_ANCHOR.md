# Major research anchor: behavior, evidence and deliberation

Recorded 26 September 2026 following the user's explicit endorsement of the [evaluation and paper-direction memo](PERSONA_EVALUATION_AND_PAPER_DIRECTION_20260923.md). This is a major project anchor and should guide subsequent experiment plans. The user subsequently authorized implementation in small increments, with something useful to learn at every step. See the [measured evaluation learning log](EVAL_LEARNING_LOG_20260926.md): source audits, a tested action scorer, empirical baselines and a seven-event development review pack are implemented. Specific training settings remain provisional; no new adapter has been run.

**Execution plan:** [Research checkpoints, calibrations and deliverables](RESEARCH_CHECKPOINT_PLAN.md), recorded 27 September, breaks the next two-event evaluation slice and the longer-term training, deliberation and publication work into small steps with explicit outputs and decision rules.

**First execution checkpoint:** [Two-event evaluation package](EVAL_PILOT_CHECKPOINT_20260927.md): source-checked reconstruction cards, seven action/eight policy pairs, exact supporting spans and a 19-example authored calibration deck. Forty-three targeted checks pass. No new model generations or independent human ratings yet; archive timing and announced-position limitations are explicit.

**Inference checkpoint, subsequently completed:** [Traced runner and bounded job payload](EVAL_INFERENCE_CHECKPOINT_20260927.md). Trillium access was restored, the checkpoint-default override was fixed, and the real 30-output baseline and diagnostic replays completed. No new adapter has been trained.

**Active priority — evaluation before training:** [Stabilization results](EVAL_STABILIZATION_RESULTS_20260927.md) and [frozen protocol](EVAL_STABILIZATION_PROTOCOL_V1.md). The 200-prompt check preserves all 14 original action outputs and passes all 18 fictional extraction controls, yet its counterbalanced mixture predicts Abstain on all seven historical decisions. Repeatability and consistency therefore cannot substitute for correctness. The proposed atomic policy rubric, source-support review kit and reviewer-agreement tooling are prepared, with 68 targeted tests passing. Independent semantic review and additional event families remain necessary; the exposed two-event slice is development-only. The user explicitly reaffirmed this evaluation gate before training.

## The question to preserve

**Does training on dated institutional behavior improve held-out decisions and policy fidelity beyond prompting the same model with the same evidence—and does any improvement carry into multi-agent deliberation?**

The target is a country–institution–date-conditioned representative. Official positions, population opinions and online community discussions are distinct objects. Reddit can support a separate discourse or stakeholder-awareness experiment; it does not supply government-policy ground truth.

**27 September clarification:** [Research goal, prompting concern and training method](RESEARCH_GOAL_AND_METHOD_20260927.md) distinguishes the application goal of useful international-policy deliberation from the three empirical claims, qualifies the Utility Engineering argument about prompting, and separates Centaur-style behavioral SFT from constitutional persona training. It proposes a false-consensus diagnostic without presuming that prompting fails or that training necessarily prevents homogenization.

Two complementary literature anchors support this direction:

- **UNBench is the main external evaluation anchor.** Use linked proposals, votes and statements, with task-specific information cutoffs. The user reports access to the authors' data. Inventory that release and resolve the scoring inconsistencies recorded in the memo before selecting baseline targets. [Paper, v2](https://arxiv.org/abs/2502.14122v2).
- **Centaur is the behavioral-training and evaluation anchor.** Borrow response-only supervision, prediction of observed behavior, tests on unfamiliar settings and the distinction between recorded-history prediction and autonomous rollouts. This is our institutional adaptation, not a claim that Centaur already validates diplomatic personas. [Nature paper](https://www.nature.com/articles/s41586-025-09215-4).

Keep three separate outcomes: documented-action fidelity, grounded policy application, and the incremental value of interaction. Fluent national style, forced disagreement and higher agreement rates do not substitute for these outcomes. A null result against a strong same-evidence baseline is scientifically useful.

## Focus now: one training method

**Recommended first method: evidence-conditioned behavioral supervised fine-tuning, using the existing LoRA implementation and pinned base model.**

Input: dated country/institution/role, the concrete task or proposal, admissible source evidence and necessary prior context. Target: the observed action or substantive attributed response. Supervise target tokens only. Keep action prediction and response reconstruction as separately tagged and separately scored tasks; a later public justification must not enter a pre-decision prediction input.

Use a shared role-conditioned adapter initially. Preserve the existing Germany/China work and all earlier releases; prepare the new pilot as a separate version. Select a narrow country/task subset after auditing independent-event and class coverage, not simply because it produces convenient examples.

| Arm | Model and input | Purpose |
|---|---|---|
| A | Untuned base + country/institution/date prompt | Measure what role prompting already achieves |
| B | Untuned base + the same role prompt + frozen dated evidence | Principal control: isolate the value of providing information |
| C | Behavioral SFT adapter + exactly B's evaluation prompts and evidence | Measure the incremental benefit of training |

This is one training method with two inference controls. Hold model revision, task definitions, evidence packets, template and decoding settings fixed where comparable. Log the additional context cost of B versus A. Compare B versus C as the primary training contrast. Do not tune A/B/C on the final test.

DPO, RL, utility rewriting, per-country adapters, context distillation and interaction training remain conditional follow-ups. The broader method list is a research roadmap, not a request to run every branch. Add one targeted comparison only when measured failures motivate it. Evidence-grounded policy-application augmentation is a later data ablation against action/response SFT; keep observed and authored supervision distinguishable.

## Next step: evaluation first, then a small experiment

Reuse the current scaffolding rather than starting from scratch: [evaluation-pack builder](../scripts/build_eval_pack.py), [review scorer](../scripts/score_reviews.py), [decision baselines](../scripts/decision_baselines.py), and [regression diagnosis](REGRESSION_RESEARCH.md). Their presence does not establish that the new benchmark, probability scorer or rubric is ready.

| Order | Concrete deliverable | Completion condition |
|---|---|---|
| 1. Audit the data and task | Full accessible benchmark inventory; documented source-time boundaries; cross-release overlap map; country/class/event counts | Target outcomes cannot enter prediction context, and all related event/document/translation derivatives are grouped before splitting |
| 2. Implement and check evaluation | Versioned schemas, action parsing/probability scoring where available, human rubric, paired reports and known-answer scorer fixtures | Deliberately wrong labels, unsupported claims, missing values, invalid outputs and empty answers receive the intended treatment; reviewer agreement is checked on a pilot |
| 3. Freeze development and final-test packs | IDs, packet hashes, gold labels/support spans, split rules and reviewer decisions | Development is available for debugging; final test is separate and locked before training-data generation or model selection |
| 4. Run A and B | Role-prompt and same-evidence baseline predictions, costs and error analysis | Verify the task is meaningful, minority actions are represented and evidence is sufficient for the intended question |
| 5. Resolve instrumentation, then run C | Generation replay where still outstanding; one small, versioned LoRA run; paired development evaluation | Record effective EOS/decoding configuration, stop reasons, supervised tokens, truncation and repetition; compare to B on identical packets |
| 6. Inspect and choose the next branch | Blinded review and an event-level paired result table | Identify a repeatable useful signal or a concrete failure mechanism before enlarging data, adding objectives or building a simulator |

The earlier 56-prompt inspection pack and exposed workshop examples are development material. They are not a new independent final test. Before another training run, inspect whether the stopping/decoding replay identified in the regression report has since been completed; do not assume either resolution or a particular causal explanation for repetition.

For a cheap pilot, aim initially at a two-country subset, roughly 100–250 reviewed training examples per country and at least 20 independent development families if the evidence supports them. Keep a separate final-test pool and report its independent family count. These are provisional engineering sizes, not power guarantees or promotion thresholds. A first small run diagnoses signal and data quality; it cannot establish broad persona fidelity. Expand independent events and repeat seeds before confirmatory claims. Record token and compute budgets after tokenization rather than reusing older cost estimates as guarantees.

## Scorecard and decision rules

For the **first single-agent pilot**, primary outcomes are held-out action NLL where valid probabilities are available, and policy fidelity pass rate. Macro-F1, balanced accuracy, no/abstain recall and unsupported commitment rate are required companions. Separate vote abstention from a model saying the evidence is insufficient. If the available interface cannot yield comparable probabilities, report that limitation and label-based results rather than inventing NLL from verbal confidence.

Policy fidelity requires supported claims, correct role/date attribution, retained material constraints and appropriate uncertainty. Score required content as well as errors so empty answers cannot pass. Inspect repetition, truncation and basic capability retention independently. Bootstrap independent event/family groups, not correlated country rows or dialogue turns. Choose practical improvement/noninferiority margins before inspecting final-test results.

**Deliberation gain at a matched compute budget remains the third project-level endpoint, reserved for the later interaction stage.** It is not part of the first SFT pilot's success claim.

- **C improves on B:** repeat on additional independent families/seeds, then test one useful data ablation. Move to controlled interaction only after individual behavior is reliable enough to interpret it.
- **B matches or beats C:** investigate evidence quality, data alignment and optimization; keep the stronger prompting/retrieval result. Do not add RL merely because SFT failed.
- **Neither B nor C succeeds:** inspect task identifiability, missing evidence and scoring before spending more on training.
- **C learns style but invents commitments:** prioritize grounded supervision and reviewed corrections; only then compare correction-SFT with DPO.
- **Individual fidelity holds but interaction harms it:** study error introduction, pressure-induced drift and unsupported convergence. Do not relabel consensus as success.

## Working paper direction

**From Positions to Decisions: Evaluating Behavior-Trained Country Personas in Multi-Agent Deliberation.**

Keep this as a working title, not a promised result. If the strongest contribution remains individual behavioral modeling and evaluation, use **Learning Institutional Behavior from Public Records: A Temporal Evaluation of Country-Persona Fine-Tuning**. The full metric and benchmark portfolio remains in the [23 September memo](PERSONA_EVALUATION_AND_PAPER_DIRECTION_20260923.md); this anchor establishes the narrower next step.


## Empirical checkpoint: 28 September

The [first measured deliberation baseline](DELIBERATION_BASELINE_20260928.md) adds evidence for evaluating national answers and final aggregation separately. The same source packet can yield correct uncertainty in a national note and unsupported certainty in the final memo. A targeted prompt change repaired two source-scope errors but introduced a new common-position claim. This does not establish a general prompting solution or demonstrate changed underlying values. It does show why behavioral training must be compared against a strong, frozen same-evidence baseline, why corrections and new errors need separate counts, and why final-answer fidelity cannot be inferred from agreement or changed wording. No trained-model improvement is claimed.
