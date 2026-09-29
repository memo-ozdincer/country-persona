# Research checkpoint plan

27 September 2026. Proposed execution plan for the [research anchor](RESEARCH_ANCHOR.md), building on the [goal and method clarification](RESEARCH_GOAL_AND_METHOD_20260927.md) and [measured learning log](EVAL_LEARNING_LOG_20260926.md). This plan records future checkpoints; it does not imply those experiments have run.

**Application goal:** improve evidence-grounded international-policy deliberation: represent institutional positions faithfully, expose tradeoffs and develop defensible options. **Research question:** does behavioral/policy training improve fidelity beyond a strong same-evidence prompt, and does that improvement help collective analysis at a matched budget?

The immediate work is a two-event evaluation slice with both action and policy-application tasks. One evidence-conditioned LoRA SFT method remains the first training intervention. Constitutional preferences, separate country adapters and interaction training are conditional branches.

## Operating rule: every checkpoint leaves something useful

Every checkpoint ends with a small artifact, a measured observation, a limitation and a next decision. Failed checks are useful outputs when they identify a defect or rule out an approach. Keep the source packet, raw outputs, errors and cost next to the aggregate score. No new dashboard or simulator is required to make progress.

**User clarification, 29 September:** run one small, interpretable checkpoint at a time and inspect it before choosing the next experiment. Do not stack speculative runs or spend this stage on multiple seeds of one experiment. Prioritize useful insight, forward progress and strong evaluation. [Aurora access, GPU snapshot, private credential locations and scratch-storage workflow](AURORA_WORKFLOW.md) are recorded separately; that access check launched no experiments.

**Aurora resource ownership:** another medical agent may use the same `memo` account. Leave its resources and all unfamiliar allocations/processes untouched. Only manage resources positively identified from this project's own launch records; never infer ownership from the username alone or perform account-wide cleanup on Aurora.

Use three kinds of calibration throughout:

1. **Evidence and reviewer calibration:** are the task, source cutoff, reference answer and rubric dependable?
2. **Model calibration:** does confidence track correctness, and does the model express uncertainty when the evidence underdetermines a policy answer?
3. **Experiment calibration:** does a claimed improvement survive the right baseline, independent events, a matched budget and a useful effect-size criterion?

Current state: benchmark acquisition/audits and the action scorer exist. The [27 September source checkpoint](EVAL_PILOT_CHECKPOINT_20260927.md) adds two source-checked reconstruction cards, seven action and eight policy A/B pairs, and a 19-example authored rubric deck. The [first measured baseline](EVAL_BASELINE_RESULTS_20260927.md) now includes an eight-output probe, the 30-output A/B comparison, an EOS-only base-model replay, 56 passing targeted checks and a 16-response review packet. Independent human reviews, new trained adapters and sealed final-test results remain outstanding. The broader development candidate pack has 21 decisions across seven meetings, not necessarily seven independent issue families. Existing Germany/China training releases remain separate.

## Phase 1: trustworthy cases and the first informative model outputs

**Current status update:** [Evaluation stabilization](EVAL_STABILIZATION_RESULTS_20260927.md) adds a frozen 200-prompt diagnostic, exact original-output replay, all-six answer mappings and an atomic policy/source review packet. All 18 fictional extraction controls pass; averaged historical predictions collapse to Abstain, so model robustness is not solved. The evaluator exposes that failure. Independent rubric/source review and new event families are the next gates; training stays deferred. There are 68 passing targeted tests, not 68 independent model-quality observations.

### 1A. Verify two contrasting events

- **Question:** can we define the target and allowed information without ambiguity?
- **Start:** S/2021/990, the climate/security proposal, and S/2022/720, the Ukraine proposal, from the exposed development candidates. These give different issue contexts and observed disagreement/abstention. Selection is diagnostic, not representative or a new hidden test.
- **Artifact:** two event cards with exact draft/stage, country/institution/date, primary vote support, pre-vote source inventory, excluded later material, and explicit unknowns. Include all usable extension-country views; do not require every country to have been a Council member.
- **Calibration:** independently check document identity and label linkage; distinguish publication date from verified availability; mark announced votes separately from predictions without an announcement. Preserve unresolved source questions.
- **Decision:** admit a case only for the task its evidence supports. An unresolved vote cannot become gold through guesswork. A retrospective case can remain useful without being labeled prospective forecasting.
- **Useful even if it fails:** a documented data defect and a precise acquisition target.

### 1B. Add policy questions to the same evidence

- **Question:** can we evaluate substance beyond a vote?
- **Initial scope:** approximately 6–10 short policy items across those two events, where sources support them. Cover position extraction/application, a documented qualification or exception, missing information, and attribution/date. Keep the observed-action question separate.
- **Artifact:** prompts, required-content checklists, supporting spans, acceptable alternative answers and a `not_established` category. Authored questions and scenarios are explicitly labeled; a new scenario does not receive an invented historical vote.
- **Calibration:** a fluent generic answer must fail when it omits a material constraint; a well-supported answer can pass despite different wording. Empty answers cannot pass. A correctly predicted vote with an invented explanation fails policy fidelity even if the action score passes.
- **Decision:** simplify or drop questions for which reviewers cannot specify defensible scoring criteria. Do not resolve an underdetermined policy by inventing a red line.
- **Useful output:** the first inspectable open-ended persona evaluation, alongside the action task.

### 1C. Test the rubric before using it to select models

- **Question:** can the evaluator reliably distinguish substantive success from plausible prose?
- **Artifact:** a small blinded calibration deck: supported answer, unsupported commitment, omitted condition, wrong institution/date, empty answer and appropriate uncertainty. These authored examples test the scorer; they are not model results.
- **Calibration:** all unambiguous seeded failures must receive their intended treatment. Two independent reviewers should initially rate the deck; record raw agreement and disagreement categories before adjudication. Assistant source checks remain distinct from human/expert ratings. As the real-output pool grows, target 20–30 double-rated outputs as an initial rubric-debugging batch, not a power guarantee.
- **Decision:** revise ambiguous criteria and repeat only the affected checks. No automatic judge becomes the final authority merely because its scores look plausible. Any model judge is calibrated against independent ratings on cases outside its training data.
- **Useful output:** rubric v1, worked scoring examples and a disagreement log.

### 1D. Run a tiny inference and decoding check

- **Question:** are the outputs and probabilities actually measuring the intended task?
- **Artifact:** the first 4–8 development generations plus token/probability traces and timing. Use the pinned base model, explicit context/output budgets and the locked chat template.
- **Calibration:** compare raw tokens and stop reasons; record every EOS setting; check full input coverage, repetition and output caps. Replay the existing stopping discrepancy before interpreting a new adapter. Never truncate a draft silently. The current preflight found a 10,687-token draft prompt; count the added evidence before fixing the total budget.
- **Action probabilities:** score the actual model's fixed legal-label distribution, report its total legal-label mass separately, and retain unconstrained invalid-output rates. Do not derive probabilities from written confidence. A conditional legal-label probability can be high even when most raw probability mass lies elsewhere.
- **Decision:** correct instrumentation before enlarging the run. No training is needed to learn from a formatting or context-budget failure.
- **Useful output:** real model examples, a functioning inference receipt, and a measured estimate of the remaining run cost.

### 1E. Compare prompting with and without evidence

- **Question:** what does admissible evidence add to the base model?
- **Arms:** A = task/proposal plus country/institution/date; B = the identical input plus a frozen dated evidence packet. Both arms use the same model, task wording and output settings. Record B's extra input cost. For policy tasks, the source-backed reference checklist is common to both arms; the comparison estimates the value of supplying that evidence.
- **Scope:** start on the two reviewed events, then expand to the usable portion of the seven-event development pack. A third neutral-role probe is optional for diagnosing role effects, not an automatic full experiment grid.
- **Artifact:** side-by-side A/B answers, action scores, policy criterion scores, unsupported commitments, costs and an error ledger per event.
- **Calibration:** retain constant-vote and training-only empirical priors as action baselines. Annotate A/B outputs with identities hidden. Tiny samples are case studies; do not headline calibration-bin statistics or significance tests from them.
- **Decision:** if B helps, identify which information mattered. If B fails, distinguish missing evidence, misreading, historical memorization, ambiguous targets and decoding faults before proposing more training.
- **Useful output:** the first empirical answer about our model and data, regardless of whether evidence wins.

## Phase 2: a clean evaluation and one interpretable training experiment

### 2A. Expand independent coverage and freeze the comparison

- **Question:** do the initial failures or gains recur beyond a few familiar events?
- **Artifact:** a reviewed train/development/test family manifest, coverage matrix and a short experiment specification. Treat all previously inspected cases as development material.
- **Initial engineering target:** at least 20 independently reviewed development families if feasible, plus a separately reserved final-test pool. Select two countries for the first training run based on usable event/evidence coverage. Training examples might initially number 100–250 per country, but family diversity and answer-token counts matter more than those row targets. These are adjustable starting sizes, not statistical guarantees.
- **Calibration:** group linked drafts, revisions, translations, recurring proposal families, country views and cross-release overlaps before generating derivatives. Test a held-out time period and issue transfer where coverage supports them. Historical data may have appeared in base-model pretraining; distinguish that evaluation from a later genuinely prospective collection.
- **Before new training:** freeze primary outcomes, country/event weighting, unacceptable regression margins and the practical benefit needed to justify cost. Choose the numerical margins using task stakes and development variability; write them down before seeing C or final-test results. Use development data to estimate whether the final-test pool can resolve the desired effect. A wide interval is an inconclusive result, not a reason to lower the bar afterwards.
- **Decision:** if a class or country lacks support, restrict the claim or acquire genuine additional events. Synthetic examples cannot fill missing historical outcome classes. Keep the final test out of prompt selection, teacher generation, early stopping and routine debugging; hash it and log access.
- **Useful output:** an evaluation package and reusable dataset-quality specification even if SFT never helps.

### 2B. Run one small behavioral SFT pilot

- **Question:** does training improve over B when evaluation evidence is identical?
- **Artifact:** one versioned shared country/role-conditioned LoRA adapter, training manifest, learning curves and a B-versus-C development report. C sees exactly B's evaluation inputs.
- **Training:** actual actions and substantive attributed responses, with response-only loss. Keep task exposure explicit so long text does not dominate short decisions. Reviewed policy-application supervision is a separate subsequent data ablation; keep authored and observed targets distinguishable.
- **Calibration:** first verify masks, label boundaries, source exclusion and loss accounting on a tiny batch. A deliberate small-batch memorization check tests implementation only, never generalization. Monitor invalid answers, repetition, truncation, unsupported commitments and a small fixed capability-retention set.
- **Budget:** initially one training configuration and one diagnostic seed. Tokenize first and record a run cap in GPU-hours/tokens before launch. Use the measured small-batch throughput to estimate cost; earlier cluster estimates are not guarantees. More seeds come after a useful signal warrants them.
- **Decision:** C must be compared with the strong same-evidence baseline, not only A or the majority vote. Training loss decreasing or national style becoming more recognizable is insufficient. If C fails, keep B as a useful system and identify one repair rather than launch an optimizer sweep.
- **Useful output:** an evidence-based answer about the value of our first training method, plus concrete residual errors.

### 2C. Test persistence, generalization and the source of any gain

- **Question:** did C learn supported policy behavior that survives changes in wording, context and pressure?
- **Artifact:** a robustness report and one targeted data-ablation result. Where C has a credible development signal, repeat on additional families and, provisionally, three training seeds before a confirmatory claim.
- **Calibration pairs:** meaning-preserving paraphrases/option order; irrelevant evidence; incorrect country/date attribution; independently supported policy updates; genuine missing information; and content-free majority pressure. A material update is scored as a required change only when the new reference is established.
- **Probability calibration:** use held-out development data for any fitted temperature/calibration mapping, freeze it before test, and show raw as well as calibrated NLL/Brier and classwise reliability where sample sizes support them. Label support and minority recall accompany every aggregate score.
- **False consensus:** among country pairs with independently supported different positions, measure incorrect convergence; also score genuine agreement cases. Report event-level rates before/after interaction later. Do not reward maximum disagreement or stereotyped national differences.
- **Ablation choice:** first test whether reviewed policy-application examples add to action/response SFT; hold action exposure fixed and include an equal-compute control when attributing an improvement to the new data.
- **Decision:** expand only the demonstrated useful ingredient. Use event/family-level paired uncertainty, not rows or dialogue turns as independent observations. State when precision is inadequate. Final-test access follows the frozen selection rule and is not repeated after every tweak.
- **Useful output:** a defensible individual-persona result, including a useful null result if prompting remains stronger.

## Phase 3: test deliberation before training it

### 3A. Build a small inspectable interaction task

- **Question:** does interaction improve a defined policy-analysis task while preserving fidelity?
- **Initial scope:** 3–5 development scenarios with explicit country briefs, common factual evidence, documented constraints, permitted actions and a clear output task. These are authored tasks, not predictions of unobserved historical negotiations. A single brief exchange is enough for the first trace.
- **Artifact:** scenario cards, complete interaction transcripts, a final options memo and independent criterion-level ratings. Score factual accuracy, constraint satisfaction, objections addressed, unresolved tradeoffs, unsupported commitments and justified updates. Use an explicit simulator/payoff only where authored rules make it defensible; archive votes do not identify real national welfare.
- **Controls:** one model analyzing all briefs; independent persona analyses combined by an aggregator; interactive personas. Freeze total evidence access and a comparable compute budget, including aggregation. Log input/output tokens and timing; extra discussion alone is not evidence of an interaction effect.
- **Calibration:** before/after source fidelity, corrections versus new errors, false consensus and unsupported concessions. A well-supported unresolved disagreement can be a successful output. For causal attribution to persona training, compare B-agent and C-agent teams in the same protocol.
- **Decision:** retain discussion only if it adds a predeclared useful task benefit without an unacceptable fidelity regression relative to the strongest matched control. Diagnose failures with short traces before increasing agents or rounds.
- **Useful output:** a working, inspectable policy workshop and a direct result about whether discussion helps.

### 3B. Train or redesign interaction only for a diagnosed failure

| Observed failure | Small next experiment | Required useful output |
|---|---|---|
| Missing or stale facts | Better dated retrieval/evidence selection | Before/after evidence coverage and affected-case outcomes |
| Supported constraints are lost in answers | Reviewed correction-SFT versus DPO on the same cases | Criterion-level change, capability retention and cost |
| Position collapses under irrelevant pressure | Source-backed constitutional/context-distillation comparison | Fidelity and justified-update tests; not merely stubbornness |
| Shared adapter mixes country positions | Better conditioning; separate adapters only as a controlled follow-up | Cross-country leakage and generalization comparison |
| Good individual outputs degrade in discussion | Change protocol first: independent initial answers, evidence-linked objections, explicit revisions | Error introduction and false-consensus changes |
| Protocol is sound but repeated interaction errors remain | Small set of independently reviewed trajectory corrections | Held-out rollout improvement at matched budget |

Preference labels and any rewards require independent validation. Optimizing an uncalibrated judge is not progress. DPO, RL, utility rewriting and more agents are not automatic milestones.

## Phase 4: generalization, human usefulness and publication

### 4A. Replicate the useful result

Expand one dimension at a time: additional independent issues, countries/institutions, policy updates and languages. Use audited translations and history/role mappings. Repeat on another suitable base model only after the first model yields an interpretable result. Add a prospective collection with predictions committed before newly observed decisions if a forecasting claim matters.

**Artifact:** transfer/robustness tables, refreshed benchmark cards and a model/evaluation card describing where the system fails. **Decision:** restrict claims to supported populations, tasks, periods and languages when transfer fails; collect targeted data rather than claim a universal country simulator.

### 4B. Check usefulness to people and make the paper reproducible

Run a bounded, blinded assessment with domain reviewers on policy-options briefs. Have them score accurate coverage, usefulness of alternatives, evidence quality and overlooked constraints, separately from prose fluency. Record inter-reviewer differences and distinguish government-policy fidelity from the desirability of a policy. Claim usefulness to policy professionals only to the extent the study supports it.

**Artifact:** reproducible code/manifests, benchmark/rubric cards, appropriately shareable examples, result tables with uncertainty and compute costs, and a paper whose title matches the strongest demonstrated result. Publish a result about data quality, persona fidelity, or a negative deliberation finding if that is what the evidence supports. Public artifacts must distinguish runnable code, verified data, unreviewed candidates and synthetic scenarios.

The existing explorer can expose approved cases, source spans, A/B/C examples and scored interaction traces as they become available. Add one useful result view at a time; raw acquisition does not automatically authorize or justify publishing every source artifact.

## Stable scorecard

| Dimension | Primary/required measure | How to read it |
|---|---|---|
| Observed actions | NLL where valid model probabilities exist; balanced accuracy, macro-F1 and minority recall alongside it | Per-country/class support and invalid rates are mandatory; report conditional legal-label semantics |
| Policy fidelity | Pass rate on applicable required criteria; component scores and unsupported commitment rate | Both supported-claim precision and required-content coverage; calibrated independent review |
| Persistence | False consensus, irrelevant-pressure flips, justified updates and paraphrase consistency | Stable wrong answers and artificial disagreement are failures |
| Deliberation | Task-score gain over the strongest frozen matched-budget control, with a fidelity regression limit | Pre/post improvement alone cannot distinguish interaction from extra computation |
| Cost and reliability | Full input/output tokens, latency/GPU time, cap/repetition/invalid rates | No benefit claim without its added cost and failure rate |

Avoid combining these into one weighted persona score that lets fluent language compensate for fabricated commitments. Practical benefit and noninferiority margins belong in the experiment specification before confirmatory outputs are inspected.

## Checkpoint receipt template

Append a short receipt to the learning log after every small step:

```text
Checkpoint / question:
Frozen inputs, source dates and hashes:
Comparison and expected diagnostic behavior:
Artifact link(s):
Actual observations, including failures and per-event examples:
Independent family counts and uncertainty/coverage limits:
Tokens, compute and reviewer time spent:
Decision: continue / repair / collect a specific missing source / keep the simpler baseline
One next question and its bounded experiment:
```

Use completed receipts as the progress measure. Calendar dates depend on evidence access, reviewer availability and the compute queue; they are not substitutes for the exit conditions. Work on source collection, implementation and diagnostic fixtures can proceed while independent reviews are pending, with their status stated honestly.

## Immediate queue

**Measured interaction checkpoint:** [28 September baseline and targeted diagnostic](DELIBERATION_BASELINE_20260928.md). The 42-call base interaction run and six-call synthesis follow-up completed. Three final memos hit their cap; exact source checks expose unsupported consensus, a position reversal and chronology errors. The targeted prompt fix also introduces a new error. Before selecting a training method, stabilize whole-answer claim review and synthesis output handling, preserve the original failures, and test the repair on a new event family. The implemented checkpoint comparator is ready for a later trained run; semantic ratings remain pending.

**Next small comparison prepared:** [Evidence-format checkpoint](EVIDENCE_FORMAT_CHECKPOINT_20260928.md). Nine calls compare prose, explicit evidence prose and JSON within the same three contexts, adding South Sudan with four complete statements and 13 source-linked proposed criteria. All prompts fit their full output allowance; 81 software tests pass. Mechanical quote checks explicitly leave entailment/completeness unscored. GPU execution and independent review are pending; preparation is not evidence of improved behavior.

**28 September implementation:** [Training readiness and bounded deliberation probe](TRAINING_READINESS_20260928.md). Local source/mask/optimizer checks pass and a retained four-H100 allocation recipe is prepared. The 42-call peer/self/central comparison, tokenizer preflight and explicit-rating workflow are ready. Independent review and infrastructure validation remain gates; the ten-case fit probe is a technical diagnostic, not a replacement for the substantive behavioral SFT study.

**New calibration gate from [the failure analysis](EVAL_FAILURE_ANALYSIS_20260927.md):** the action interface is sensitive to country-name and answer-format changes. Before a new SFT experiment, separate source sufficiency from recorded-vote prediction, predefine and check prompt invariance, and include the stronger source-grounded prompt as a comparator. The 34 targeted diagnostics do not replace independent policy ratings or establish a new benchmark score.

- [x] Two assistant source-checked event cards for S/2021/990 and S/2022/720; admitted as historical reconstruction, with archived-version availability and independent review explicitly unresolved.
- [x] Eight grounded policy items and an initial reference/rubric deck.
- [ ] Reviewer/scorer calibration: 19 authored scoring fixtures checked; independent human ratings/agreement still pending.
- [x] A real eight-output inference/decoding check and measured run cost. A checkpoint-default override was caught and fixed before expansion. Default/legacy EOS lists produce identical base-model outputs on these eight inputs. The earlier trained-adapter repetition remains a separate diagnostic before new adapter interpretation.
- [ ] First side-by-side A/B action **and** independently rated policy report: [30 outputs, action scores and source-checked policy observations are complete](EVAL_BASELINE_RESULTS_20260927.md); independent policy criterion ratings remain pending. Expand through the seven-event pack only as its records clear review.

The first useful delivery is the two event cards and worked scoring examples. The first model milestone is an interpretable A/B comparison. Neither requires completing the long-term training or deliberation system.
