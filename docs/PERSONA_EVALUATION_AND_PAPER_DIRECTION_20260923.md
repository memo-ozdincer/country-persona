# Persona fine-tuning and deliberation: evaluation and paper direction

Research proposal, 23 September 2026. No scores, successful training runs, or newly validated benchmarks are claimed in this memo. Suggested targets and sample sizes are design choices to pilot, not established standards.

**Status, 26 September:** The user explicitly endorsed this direction as a major research anchor. The [anchor and narrow pilot sequence](RESEARCH_ANCHOR.md) preserve that decision and recommend focusing first on evaluation plus one behavioral SFT method. The broader methods and benchmarks below remain staged possibilities.

## Recommendation

**Working title: _From Positions to Decisions: Evaluating Behavior-Trained Country Personas in Multi-Agent Deliberation_.**

The central question should be: **Does training on dated institutional behavior improve held-out decisions and deliberation beyond a prompted model with the same evidence?**

This separates three empirical claims: (1) reproducing documented behavior, (2) applying documented policy to new cases, and (3) improving interaction. A model can succeed at one and fail at another. Give each a separate result table. A negative deliberation result can still make a useful paper if its controls establish why better individual personas do not improve collective outcomes.

Our object is a country–institution–date-conditioned representative. It is neither a country's average resident nor the personality of a named diplomat. Track ministries, UN delegations, historical entities and institutional powers explicitly. The existing country coverage is useful, but Germany, India and Brazil only vote in the UNSC during membership terms; being a nonmember is not abstention. Do not silently map pre-1971 Chinese representation to the PRC or historical Soviet behavior to present Russian policy.

## Reading record and what to borrow

Downloaded the explicitly requested [UNBench v2 PDF](https://arxiv.org/pdf/2502.14122v2) to `research/persona-evaluation-20260923/2502.14122v2.pdf`. Read the task definitions, construction, experiments and appendices, and visually checked the result tables. Extracted all five unique PDFs in `/Users/memoozdincer/Downloads/possibly_interesting`; the two `2026.mme-main.10` files are byte-identical. File hashes, source paths and page counts are in `research/persona-evaluation-20260923/manifest.json`. Read the relevant methods, evaluation and limitations of these five papers. The broader benchmark shortlist below was checked against primary paper/author pages; it is not a claim of full replication of each benchmark.

| Supplied paper | Contribution to this project | Boundary |
|---|---|---|
| [UNBench: Benchmarking LLMs for Political Science](https://arxiv.org/abs/2502.14122v2) | Main external benchmark: co-penholder identification, individual votes, adoption and statements | Static linked tasks do not themselves test interactive deliberation |
| [Centaur: A foundation model to predict and capture human cognition](https://www.nature.com/articles/s41586-025-09215-4) | Train on observed responses with context loss masked; evaluate response likelihood, held-out settings and autonomous rollouts | Behavioral modeling, not a demonstrated method for eliciting national personas |
| [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) | Independent diplomatic role-play and multilingual vote benchmark, with contentious cases | P5-only; historical entities and overlap with UNBench need auditing |
| [Utility Engineering](https://arxiv.org/abs/2502.08640v1) | Pairwise preference elicitation, utility-model fit and preference-distribution training | Coherent model choices do not identify a government's hidden utility; simulated citizens are not surveyed humans |
| [RAFT](https://arxiv.org/abs/2403.10131v2) | Train with relevant evidence and distractors; compare against retrieval-only prompting | Its original answer-memorization component needs a separate ablation; dated policy should not be recalled over a verified update |
| [Legal Judgment Prediction: If You Are Going to Do It, Do It Right](https://aclanthology.org/2023.nllp-1.9/) | Audit what information existed before an outcome | Post-decision reconstructions must not be sold as prospective prediction |

### UNBench: use it, and audit the exact evaluation implementation

V2 describes 1994–2024 UNSC data and four tasks. Table 1 reports 1,300 drafts for co-penholder tasks; 17,430 votes from 1,162 drafts; 1,978 adoption examples; and 7,394 statements. Its statement task explicitly permits the vote outcome and previous statements as input (section 3.2): appropriate for retrospective explanation, not pre-vote forecasting. The authors describe a chronological minority-label-based split; reproduce and inspect its actual event boundaries.

There are reporting inconsistencies worth resolving before choosing a target score: Table 2 gives GPT-4o Task-2 balanced accuracy 0.823, but Appendix Table 8, labeled Task 2, gives 0.677. Appendix Table 9 gives 0.823 for Task 3. The three vote counts in Table 1 sum to 17,427, three short of the stated total. These are audit flags, not evidence of a particular cause. Recompute from the release and code; do not silently choose one table. [Paper](https://arxiv.org/abs/2502.14122v2), [author repository](https://github.com/yueqingliang1/UNBench).

The user reports access to the authors' data. Earlier local notes only established acquisition of the public sample; before running experiments, inventory the full accessible release, hashes, labels, split IDs and task scripts. Do not equate the sample with the full benchmark. Preserve an original-protocol result for comparison and publish our stricter event/time/family evaluation separately, with its own name. Inspect candidate construction and label mapping rather than treating multiple-choice distractors as real negotiated alternatives. Recompute always-yes/always-adopt and simple supervised baselines on the actual split. All author-country derivatives of one draft belong together.

### Centaur: the most useful training analogy

Centaur transcribes trial histories into text and fine-tunes Llama 3.1 70B with QLoRA, masking all tokens except human responses. The paper uses response negative log-likelihood, a held-out-participant split, new experimental settings and simulations feeding the model's own responses back into context. Its methods specify one epoch and rank-8 adapters. These facts support a behavioral-training analogy; neither the hyperparameters nor psychological generalization results establish a diplomatic recipe. [Paper](https://www.nature.com/articles/s41586-025-09215-4).

Our proposed analogue is `dated role + available information + observed history → next documented action/response`. Supervise only the action or attributed response. Chronological diplomatic events replace experimental trials. Test both predictions under recorded histories and autonomous interaction under explicitly specified rules. Keep psychological response distributions, official institutional choices and online-community text separate. A prompted interview about what an agent “believes” is a useful elicitation probe, but is not behavioral validation.

### Utility Engineering: useful elicitation, with explicit external validation

The supplied v1 fits a Thurstonian random-utility model to repeated pairwise choices. Its appendix also describes a synthetic assembly, soft-target preference supervision and an instruction-preservation term. The demonstration uses census-conditioned simulated agents; demographics alone do not validate their opinions. [Paper](https://arxiv.org/abs/2502.08640v1).

Our adaptation: compare matched policy options with the country, institution, date and assumptions fixed; randomize option order and paraphrase; estimate uncertainty; then test whether inferred preferences predict independent observed decisions. Leave held-out outcome families, not just randomly held-out pairs. Call the result a model preference profile or policy-consistent ranking. Only use cardinal utility metrics in controlled environments whose payoff functions we specify, never infer interpersonal welfare or real national utilities from arbitrary latent scores.

## 1. Metrics: a small primary scorecard and broad diagnostics

Pre-register three primary endpoints: **held-out action NLL**, **policy fidelity pass rate**, and **deliberation gain at a matched budget**. Treat macro-F1 and minority-action recall as mandatory companion measures. Avoid a weighted “persona quality” total: a model should not offset fabricated commitments with pleasant prose. A large diagnostic suite helps explain results, but increases multiplicity and should not become a menu for selecting favorable findings.

### A. Documented behavior and calibration

| Metric | Operational definition | Role / limitation |
|---|---|---|
| **Action NLL ↓** | `mean[-log p(observed action | allowed pre-decision input)]` | Primary behavioral fidelity; report per country and macro-average across countries |
| Macro-F1 ↑ | Unweighted mean F1 over yes/no/abstain, plus per-class values | Mandatory; majority decisions must not dominate |
| Balanced accuracy ↑ | Mean recall across evaluated classes | Mandatory imbalance check; publish support counts and handling of absent classes |
| Minority-action recall ↑ | Recall of no and abstain separately | Tests meaningful boundaries rather than generic agreement |
| Multiclass Brier ↓ | Mean of `sum_k (p_k - 1[y=k])²` | Proper score of accuracy and confidence; state normalization |
| Classwise average precision ↑ | One-vs-rest average precision from probabilities | Report each class and macro mean; random baseline depends on prevalence |
| Calibration error ↓ | Reliability plots and predeclared-bin ECE | Diagnostic only; bins/sample size can change ECE markedly |
| Selective risk ↓ | Error among answered cases as coverage varies | A model may say evidence is insufficient; distinguish this from a recorded abstention vote |
| Per-country / worst-group score | Country × task × language × era × topic, with counts and intervals | Exposes concentrated failures; tiny groups cannot support rankings |
| Adoption balanced accuracy / NLL | Separate model prediction of adoption from deterministic rule application to observed votes | Do not count procedural arithmetic as successful political forecasting |
| Co-penholder accuracy / MRR | Accuracy for original choice task; MRR only for a separately defined ranking task | Randomize positions; distinguish observed sponsors from “optimal allies” |
| Role-conditioned gain | NLL or F1 change against neutral and country-only prompts | Shows what country conditioning adds; does not require disagreement where countries historically agree |

For controlled open-model comparisons, score a fixed legal action vocabulary, checking tokenization and aliases. If renormalizing over legal labels, say so and separately report invalid generated-output rate. Do not treat an LLM's written “90% confidence” as a calibrated probability. For APIs without suitable log probabilities, report label metrics and repeated-sample estimates with uncertainty; do not claim token-level NLL. Pre-register country and event weighting. Under extreme label imbalance, an NLL improvement alone is insufficient evidence of better minority behavior.

### B. Policy fidelity, grounding and persistence

Build an independently annotated set with supporting spans, issue/date/role, required conditions and explicit `not established` judgments. Reviewers must distinguish a claim supported by an institution's statement from an independently true claim about the world.

| Metric | Operational definition | Role / limitation |
|---|---|---|
| **Policy fidelity pass rate ↑** | Fraction of cases satisfying every applicable required criterion: correct attribution/date, supported claims, retained material exceptions, no invented commitment, and appropriate uncertainty | Primary; freeze the rubric first and also publish each component |
| Claim support precision ↑ | Supported checkable claims / all checkable claims | Pair with required-fact recall to prevent empty answers from scoring well |
| Required-fact recall ↑ | Relevant reference facts/constraints retained / required facts/constraints | Annotate acceptable paraphrases and multiple defensible answers |
| Unsupported commitment rate ↓ | Answers that invent an obligation, vote, red line or policy change / evaluated answers | High-impact fidelity failure; evaluate separately from ordinary factual mistakes |
| Attribution and temporal accuracy ↑ | Correct institution, speaker role and effective policy period | Crucial for mixed ministries, historical eras and evolving policy |
| Constraint/exception retention ↑ | Applicable annotated conditions retained / applicable conditions | A model can repeat a slogan yet reverse its practical meaning |
| Citation precision / recall ↑ | Correct support for cited claims; coverage of claims needing support | A real document URL alone does not establish support |
| Contradiction rate ↓ | Contradictions of the allowed evidence or established commitments | Verify legitimate updates before labeling contradictions |
| Justified-update success ↑ | Correct revision after a verified, material policy/evidence update | Needs gold revised interpretation; not every clause edit determines a unique vote |
| Irrelevant-pressure flip rate ↓ | Changed decision under a content-free authority/majority/persona-pressure manipulation | Paired with update success so stubbornness is not rewarded |
| Paraphrase and option-order robustness ↑ | Equivalent-case label agreement and probability divergence | Report accuracy as well; consistently wrong is not good |
| Cross-language consistency ↑ | Agreement / Jensen–Shannon divergence on aligned translations | Accompany each language's accuracy and translation audit |
| Long-horizon role retention ↑ | Applicable constraints retained over turns, with legitimate updates handled | Plot by turn and topic, not only a terminal judge score |
| Cross-role leakage ↓ | Uses another actor's private information or attributed commitment without authorization in the scenario | Requires explicit visibility logs and role-specific briefs |
| Blinded expert preference ↑ | Pairwise preference for source-faithful usefulness, with ties allowed | Separate fluency from correctness; randomize side/order and hide model identity |
| Judge agreement | Inter-rater agreement, judge-vs-human confusion matrix and uncertainty | Validate the evaluator; high agreement does not by itself prove a rubric is valid |

ROUGE, BERTScore/Sentence-BERT similarity, style identification and perplexity can be supplementary. None establishes decision fidelity: a polished generic speech can resemble the reference while taking the wrong position. Do not use country-name classification as the main persona score; it can reward stereotypes or trivial name leakage.

### C. Multi-agent deliberation: fidelity and task quality are distinct

Use two tracks. **Historical replay** asks whether agents reproduce recorded behavior under recorded information. **Controlled interaction** asks whether communication improves an explicitly defined task. Historical adoption is not a label for what *would* happen after an invented amendment or agent speech.

| Metric | Operational definition | Role / limitation |
|---|---|---|
| **Deliberation gain ↑** | Task score of interactive team minus a development-selected, compute-matched control on the same test cases | Primary interaction endpoint; report pre/post change too, but pre/post alone confounds extra compute |
| Error correction rate ↑ | Initially wrong → finally correct / initially wrong | Requires a verifiable task label or independently accepted interpretation |
| Error introduction rate ↓ | Initially correct → finally wrong / initially correct | Detects persuasion that worsens answers |
| Evidence uptake ↑ | Newly available, valid decision-relevant evidence correctly incorporated / opportunities | Needs labeled evidence revelation and visibility; rewards content, not agreement |
| Objection resolution ↑ | Material objections adequately addressed / material objections | Explicit unresolved disagreement is acceptable when evidence does not settle it |
| Procedural validity ↑ | Actions and transitions permitted by scenario rules / all attempted actions | Report malformed actions separately; rules must match the era/institution |
| Mandate violation rate ↓ | Agent turns or agreements violating explicit role constraints | Keep descriptive historical fidelity distinct from an idealized mandate benchmark |
| Information-boundary violation ↓ | Uses inaccessible private information / evaluated opportunities | Check role-specific logs and accidental prompt leakage |
| Unjustified convergence ↓ | Agents abandon supported differences without new evidence or an allowed concession | Measure on annotated disagreement cases; raw diversity is not inherently desirable |
| Supported-disagreement preservation ↑ | Required distinct positions surviving irrelevant pressure | Include agreement cases too; do not reward manufactured polarization |
| Partner/order robustness ↑ | Performance across held-out partner models, speaker orders and seeds | No dependence on a single cooperative judge/partner |
| Agreement / impasse rate | Report separately for feasible-agreement and genuinely incompatible scenarios | Agreement alone is not success; some principled impasses are correct |
| Joint surplus / Pareto efficiency ↑ | Utility above specified disagreement payoffs; whether a feasible Pareto improvement remains | Only for games with known utilities and feasible outcomes; not historical diplomatic welfare |
| Minimum participant surplus / Nash product ↑ | Worst normalized gain and product of gains over stated disagreement payoffs | Cardinal scales and feasibility must be specified; never apply directly to arbitrary ordinal utilities |
| Invalid concession / false promise rate ↓ | Unsupported commitments made to obtain agreement | A useful counterweight to agreement and payoff metrics |
| Rollout distribution fit | Compare simulation distributions of admissible action patterns to held-out observations | Only where observational context is comparable; changed histories remove exact counterfactual gold |
| Efficiency | Tokens, calls, latency, GPU-hours and quality-versus-budget curves | Report system-wide totals including judge, retrieval and regeneration costs |

A useful ablation panel is: one agent; one agent with iterative self-review; independent agents plus a fixed aggregator; communicating agents with identical roles; communicating agents with country-specific roles. Give all systems the same base checkpoint and permissible evidence. Compare both dispersed-information and pooled-information controls so a benefit is not just access to more documents. Match total token/tool budgets and report wall-clock latency separately. Freeze partner pools and scoring rules before the test; agents should not share hidden state.

### D. Preference-profile diagnostics (exploratory)

Borrow the measurement pattern from Utility Engineering: held-out pairwise-choice log loss, pairwise accuracy, triad cycle rate, paraphrase/order stability and within-profile rank consistency. Add our external validation: does the fitted profile improve prediction of withheld observed choices beyond country-majority and text baselines? Transitivity is a consistency diagnostic, not proof that a preference is true, desirable or institutionally grounded. Fix date, feasible options and assumptions across comparisons. Do not force uncertain historical preferences into a total ordering.

## 2. Benchmark portfolio

The recommended minimum is **UNBench + UNSC-Bench + our dated-policy stress set**, followed by **our controlled deliberation set + one external interaction benchmark** if the paper makes a multi-agent claim. Additional suites are useful diagnostics, not interchangeable measures of country fidelity.

| Benchmark / resource | Priority | What to measure | Scope and readiness |
|---|---|---|---|
| [UNBench](https://arxiv.org/abs/2502.14122v2) | Core external | Votes, adoption, sponsorship, statements | User reports data access; inventory full release and resolve scoring inconsistencies |
| [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) | Core external | Macro-F1, minority-class recall, country-role gains and language robustness | 469 resolutions, 2,345 P5 votes, four languages; 211 vetoed / 258 adopted cases. Overlaps UNBench historically; decontaminate across both. Only China/France/UK among our six are P5 |
| Dated Policy Fidelity set — proposed | Core new | Scope, conditions, attribution, calibrated uncertainty, updates and distractors | Curate from reviewed official source packets; existing explorer illustrations are not an independent test set |
| Cross-institution UPR action set — proposed | Transfer | Support/noted response labels and attributed recommendations | Use held-out country-review cycles, verify chronology; recommendation author differs from reviewed state; labels do not prove implementation |
| Diplomatic Deliberation set — proposed | Core new if claiming deliberation | Task gain, mandate adherence, objections, evidence use, valid transitions | Controlled scenarios with explicit observation boundaries and outcomes; label invented utilities and transitions |
| [SOTOPIA / SOTOPIA-hard](https://arxiv.org/abs/2310.11667) | External interaction | Social goal completion and interaction quality under its native rubric | Social interactions, not diplomatic truth. Human-audit model judges, especially after social training |
| [NegotiationArena](https://arxiv.org/abs/2402.05863) | External interaction | Bargaining outcomes, efficiency, tactics and failures | Known game settings make outcome scoring more interpretable; not a geopolitical simulator |
| [MultiAgentBench / MARBLE](https://aclanthology.org/2025.acl-long.421/) | Broader interaction diagnostic | Task completion and milestone-based collaboration/competition measures | Useful topology/coordination comparison; broad engineering scenarios do not establish national fidelity |
| [MAgIC](https://aclanthology.org/2024.emnlp-main.416/) | Optional game diagnostic | Cooperation, coordination and rationality under explicit games | Game-specific capabilities; do not interpret deception success as generally good diplomacy |
| [RoleBench / RoleLLM](https://aclanthology.org/2024.findings-acl.878/) | Role capability diagnostic | Native role knowledge/style evaluations; retention after adaptation | Character roles, not official country-policy ground truth |
| [InCharacter](https://aclanthology.org/2024.acl-long.102/) | Elicitation-method inspiration | Interview consistency; adapted evidence-linked policy interviews | Psychological character profiles do not justify assigning Big Five traits to states |
| [GlobalOpinionQA](https://arxiv.org/abs/2306.16388) | Separate population track | Survey response-distribution alignment by country/wave; add JSD or total variation with sampling intervals | Measures surveyed populations, not ministries or Reddit users. Preserve weights, dates and instrument structure |
| [CulturalBench](https://arxiv.org/abs/2410.02677) | Cultural knowledge diagnostic | Native benchmark scoring, disaggregated by region | Knowledge is different from preferences; inspect actual six-country coverage |
| [BLEnD](https://arxiv.org/abs/2406.09948) | Cultural/language diagnostic | Everyday knowledge in short-answer and MCQ formats | Benchmark covers selected regions/languages, not necessarily all project countries |
| [Psych-101 / Centaur](https://www.nature.com/articles/s41586-025-09215-4) | Methodology / optional transfer | Response likelihood and autonomous behavior under documented paradigms | Large-scale psychological benchmark; not necessary for the diplomatic paper's headline claim |
| Utility elicitation battery — adapted | Exploratory new | Held-out pairwise log loss and consistency; external choice prediction | Adapt [Utility Engineering](https://arxiv.org/abs/2502.08640v1); new country version needs independent validation |
| General capability retention | Guardrail | Fixed instruction-following, reasoning and multilingual test subsets chosen before training | Track regressions on the base model's intended uses; do not let persona scores hide general degradation |

SOTOPIA-π is a **training method**, not an additional independent benchmark. Its reported evaluator overestimation makes an independent human audit especially relevant. [Paper](https://aclanthology.org/2024.acl-long.698/). Similarly, RAFT and Open Character Training belong in the method comparison, not the benchmark count. More names are not more independent evidence: overlapping UNSC events, translated copies and generated derivatives must be grouped before any training/test assignment.

## 3. Concrete training approach

Use a shared institution/country/date-conditioned adapter first, with per-country adapters as a comparator. Keep the same underlying checkpoint and admissible evidence across comparisons. The interesting combination is **behavioral response training + evidence-grounded policy application**, then a test of whether those benefits survive interaction.

| Arm | Training / inference | Main hypothesis |
|---|---|---|
| A | Untuned model + country/institution/date instruction | What does role prompting already achieve? |
| B | Untuned model + dated brief and retrieval | Does supplying the evidence solve most errors? |
| C | Response/action-only SFT on admitted observed examples; same retrieval as B | Centaur-inspired behavioral supervision improves held-out actions |
| D | C + reviewed policy-application SFT with evidence distractors | Policies generalize beyond direct action imitation |
| E | D + correction-SFT versus D + DPO on the same reviewed failures | Preference training adds something beyond learning the corrected answer |
| F | D + selected interaction/revision trajectories | Behavior persists and improves under autonomous dialogue |
| G, optional | Distill a stable institutional brief; changing facts still retrieved | Fidelity can persist with less prompt context without losing updateability |

A role-conditioned instruction pipeline is supported by [RoleLLM](https://aclanthology.org/2024.findings-acl.878/); evidence-with-distractors by [RAFT](https://arxiv.org/abs/2403.10131v2); filtered social interaction training by [SOTOPIA-π](https://aclanthology.org/2024.acl-long.698/). These are precedents in their respective domains, not confirmed country-persona results. [Open Character Training](https://arxiv.org/abs/2511.01689) offers a constitutional persona comparator, but its DPO-then-introspective-SFT recipe differs from our proposed order. Replace personality claims with verifiable dated policy clauses; avoid inventing officials' inner beliefs.

For D, adapt RAFT carefully: distractors can be a different country's policy, an obsolete policy or an irrelevant section. When the available packet is insufficient, supervise an appropriately limited answer. The original RAFT paper sometimes retains a target without its supporting document to encourage memorization; this is a separate optional ablation, not our default for changing institutional policy. Mask source context from SFT loss. Treat a source-grounded explanation as an authored account, not proof of the historical actor's internal reasoning.

For C versus D, hold decision examples fixed and add an equal-compute action-only control to disentangle more tokens from useful auxiliary supervision. For E, preserve the same correction cases, evidence and review labels. For F, compare against an equal-token noninteractive correction curriculum; otherwise more supervision is confounded with interaction. Use learning curves and a small pilot before combining objectives or scaling.

### Where Reddit fits

The acquired collection contains 2,470,215 records and overlapping observed reply pairs, with very unequal country coverage. It supplies community discourse, not official foreign-policy labels or a representative national sample. Current prepared records remain unadmitted research candidates.

Potential distinct tasks: grounded thread summarization; identifying supported/unsupported claims; reconstructing explicit objections and replies; discussion moderation/revision; community-conditioned discourse modeling with the sampling frame stated. Preserve thread grouping, timestamps and missing-context flags. Reddit votes do not define factual correctness, preference gold labels or population support. Do not train a diplomatic persona to treat a popular Reddit reply as its government's commitment.

An interesting ablation is official evidence alone versus official evidence plus a clearly labeled community-objection packet. Score whether the agent understands public concerns while preserving attribution and institutional commitments. This is a stakeholder-awareness hypothesis, not a claim that Reddit measures public opinion. The existing synthetic bus-discussion illustrations demonstrate formats only and must not be counted as empirical evaluation examples.

## 4. Proposed new tests we can build

**Dated Policy Fidelity pilot:** start with 20 independent policy families per country across the six countries, subject to finding enough clean evidence. For each family author six linked variants: straightforward application; scope/exception; irrelevant or wrong-country evidence; obsolete versus verified updated policy; insufficient information; irrelevant majority/authority pressure. That is 120 families and up to 720 prompts, not 720 independent observations. Review the gold labels independently of the target-generating model. This is an annotation pilot, not a powered final benchmark; estimate variance and cluster dependence before setting the final size.

A concrete instance can build on the existing German critical-inputs policy: a proposal to diversify a concentrated supply chain, a purported mandate to ban all Chinese trade, an invented numerical cap, and a revised dated policy packet. Gold judgments distinguish supported diversification from unsupported bans or precise thresholds. Do not manufacture a gold contract-approval decision where the policy does not specify one.

**Controlled deliberation pilot:** 24 independent scenario families, three documented-role agents, a fixed five-round maximum, and three seeds/orders per configuration. These are provisional cost estimates, not statistical-power guarantees. Include eight complementary-evidence tasks, eight feasible bargaining tasks with declared synthetic payoffs, and eight cases with legitimately incompatible constraints. Use separate task metrics for these strata; do not average their unlike outcomes into one unexplained score. Add held-out partner models after the pipeline works.

For a complementary-evidence scenario, each agent sees a different verified clause; the task is to produce a proposal satisfying all applicable constraints or explicitly report infeasibility. Score constraint coverage and invalid commitments. The pooled-information single agent sees all clauses and receives the same aggregate compute budget. This isolates what communication contributes beyond additional information.

For historical replay, use actual draft and statement chronology. Evaluate next observed actions under real histories, but once model-generated interaction changes the trajectory, stop treating the recorded final vote as the unique correct counterfactual outcome. New branches can be assessed for source consistency and rule validity, with synthetic outcomes clearly labeled.

## 5. Protocol, statistical decisions and success criteria

1. **Define the information cutoff.** Keep draft text, publication/availability timestamps and statement ordering. Separate pre-vote prediction from post-vote explanation. The legal-prediction critique is directly applicable: summaries written after an outcome can encode it even after the label is removed. [Medvedeva and McBride](https://aclanthology.org/2023.nllp-1.9/).
2. **Group before splitting.** Join resolution IDs, related draft versions, recurring proposal families, source documents, translations, statements and synthetic derivatives. Audit overlap across UNBench, UNSC-Bench and our training corpus. Shared UN documents can contaminate an ostensibly external benchmark.
3. **Keep two evaluation protocols.** Reproduce the authors' protocol where available; separately run strict temporal and held-out-family evaluation. Label historical reconstruction honestly because a model may have seen old documents in pretraining. A claimed prospective test needs events collected after the frozen model/evaluation setup.
4. **Make baselines hard to beat honestly.** Country-majority and always-yes baselines; a train-only historical-neighbor/text classifier; role prompting; identical dated retrieval; equal-compute noninteractive models; country adapter versus shared adapter. Choose hyperparameters and the principal matched control using development data.
5. **Use the right unit of uncertainty.** Paired cluster bootstrap by resolution/family or independent scenario, not by correlated country rows or dialogue turns. Report country macro-averages, numbers of independent events, seeds and intervals. Separate within-model decoding variability from training-seed variability. Use at least several training seeds for confirmatory comparisons when feasible.
6. **Limit confirmatory claims.** Pre-register the three primary endpoints and direction, analysis weights, exclusion criteria and practical margins. Use a declared multiplicity adjustment for confirmatory families; mark additional metrics exploratory. Derive noninferiority tolerances for regressions from a pilot and stakeholder needs before seeing test results.
7. **Calibrate the judge.** Begin with a balanced pilot of independently rated outputs, two blinded reviewers and adjudication. Include correct but stylistically unusual responses and fluent errors. Report rater agreement and classwise automated-judge error. Freeze the rubric and judge before the test; do not train and evaluate on the same judge's unvalidated preferences.
8. **Publish failures.** Include role drift, unjustified convergence, wrong-date policy use, hallucinated commitments, poor minority-action recall and partner exploitation. A fixed held-out test should not become an iterative teacher-data source.

**Evidence for successful persona tuning:** positive held-out improvement over the same-evidence prompted baseline in action NLL, corroborated by macro-F1/minority recall, plus higher policy fidelity without a predeclared material regression in unsupported commitments or general capability. No arbitrary universal “80% persona score” is justified.

**Evidence for successful deliberation:** positive task-quality gain over the dev-selected matched-budget control, without material degradation of mandate adherence or evidence integrity, replicated across scenario families and partner/order settings. More consensus, more persuasive language or more tokens are not sufficient.

## 6. Paper direction and titles

**Recommended broad title:** _From Positions to Decisions: Evaluating Behavior-Trained Country Personas in Multi-Agent Deliberation._ It states the object of study without asserting an unmeasured improvement.

**Tighter first-paper title:** _Learning Institutional Behavior from Public Records: A Temporal Evaluation of Country-Persona Fine-Tuning._ Use if the strongest contribution is behavioral training and reliable evaluation, with interaction as a smaller extension.

**Deliberation-focused title:** _When Does Persona Fidelity Improve Deliberation? Evidence from Diplomatic Decision Tasks._ Use if the interaction experiment is adequately powered and central, including a meaningful null finding.

**Benchmark-led title:** _Beyond Diplomatic Style: Benchmarking Decisions, Policy Fidelity, and Deliberation in Country Agents._ Use if new reviewed tests and evaluation design contribute more than the training recipe.

The clearest contribution bundle is: an evidence-linked behavioral training release; a temporal/family evaluation protocol covering actions and policy; and a controlled test of whether individual fidelity transfers to collective behavior. Avoid a “foundation model of diplomacy” claim until there is much broader transfer evidence. Avoid “digital twins of countries”: public statements and votes do not identify a country's population, private motives or complete decision process.
