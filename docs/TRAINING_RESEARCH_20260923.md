# Training country personas from decisions and mission statements

Research memo, 23 September 2026. Based on inspection of the local exports, existing experiment reports, and the primary sources linked below. Recommendations are proposed experiments, not measured improvements. No training was launched or admission flags changed.

**Recommendation.** Build an evidence-conditioned, country/institution/date-conditioned model using supervised learning on authentic decisions and reviewed policy applications. Keep two objectives explicit: predicting observed actions and applying declared policy. Start with LoRA SFT; add evidence-adjudicated preferences only where SFT has identifiable failures. Use a constitutional classifier as a separate policy-consistency verifier if useful. Keep changing policy documents available through retrieval. Neither raw speech imitation nor an automatically generated constitution is sufficient evidence that a model reproduces diplomatic decisions.

**What is actually available locally.** Counts below were checked directly against JSONL files; quality findings come from the linked project reports. This was a targeted inspection, not a new exhaustive semantic audit.

| Material | Current evidence | Suitable objective |
|---|---|---|
| Authentic spokesperson Q&A | 8,095 training rows in `posttraining-qwen3-v1/shared-all.train.jsonl`; balanced export has 832 | Role-specific response imitation, preferably with independently available supporting evidence |
| UN mission documents | 962 China and 452 Germany canonical records, labeled `statement_reconstruction` | Source-grounded position extraction/application; selected speech generation as an auxiliary task |
| Detailed decisions | 12 country–event records, six countries, only **two events**; China/Germany conversational projection has eight rows | Format demonstration now; action imitation after expansion and review |
| Canonical UNGA decisions | 16,130 China/Germany records; inspected record is explicitly `vote_label_only`, with missing proposal text | Join proposals and prior context before action training; preserve historical entities |
| Country knowledge examples | Three authored evidence-conditioned examples | Useful task design seeds, not an independently validated behavioral dataset |
| Four-country extension | 12 policy claims and 12 authored applications | Grounded policy application, with synthetic provenance retained |
| Policy workshop | 20 audit + 10 revision + 13 role-specific SFT rows, plus ten DPO pairs | Verifier/correction/preference prototypes; ten underlying cases, eight documents, only four connected split components |

The rich decision and policy-workshop candidates remain quarantined. Alternate formats, translations, and authored scenarios increase training exposures, not the number of independent observations. “Mission statements” also needs disambiguation: a UN mission's event speech is not necessarily an enduring institutional charter.

The [pilot diagnosis](REGRESSION_RESEARCH.md) reports repetition increasing from 0 to 13 of 56 diagnostic outputs after the 500-example Qwen3 run. Its exhaustive token/mask audit passed. This supports diagnosing decoding and supervision before scaling, but does not establish a unique cause. [Existing decision format](DECISION_POSTTRAINING_FORMAT.md); [workshop provenance](POLICY_WORKSHOP_POSTTRAINING.md).

**The three learning targets must remain distinct.**

1. **Behavioral fidelity:** given the information available at a decision time, assign probability to the action the institution actually took.
2. **Declared-policy fidelity:** interpret and apply its published principles, preserving qualifications and unresolved tradeoffs.
3. **Strategic effectiveness:** negotiate to improve an explicitly defined outcome in an interactive environment.

Observed choices supervise the first. Policy documents supervise the second. The third needs trajectories, an environment, and defensible objectives that this archive does not yet supply. Governments can act inconsistently with public principles; record that discrepancy rather than forcing one signal to override the other. Matching an expert's decision also differs from proving that decision was optimal.

**Training on decision cases.**

The closest useful training precedent is Binz et al., **Centaur / A foundation model to predict and capture human cognition** (Nature, 2025). They express experimental histories in natural language, fine-tune Llama 3.1 70B with QLoRA, and mask loss except on human responses. Psych-101 contains over ten million choices across 160 experiments; evaluation includes held-out participants and task generalization. This supports response-only behavioral learning, not any claim that our two diplomatic events are sufficient. [Paper](https://www.nature.com/articles/s41586-025-09215-4).

For our action task, use:

```text
Input: country + institution + as-of cutoff + actual proposal/options
       + relevant prior public evidence + legitimate prior decision history
Target: observed action
Metadata outside target: event/source family, label provenance, availability times
```

Minimize `L_action = -mean_event(log p(observed_action | admissible_context))`, with country/task sampling explicitly specified. A classification head or constrained choice output is appropriate; a general conversational model can use short label completions. If comparing labels with different token lengths, score complete labels with their terminators and normalize across the mutually exclusive choices; do not compare only their first token. Calibrate probabilities on development data.

A long explanation should not overwhelm a one-token decision in the loss. Either train action-only and explanation tasks separately, or explicitly average their losses and tune the task weights on development data. Do not silently let document length choose the objective.

Build two different tasks from an explained vote:

| Task | Inputs | Target |
|---|---|---|
| Predict the action | Only information available before the chosen cutoff | Recorded vote |
| Report the public justification | Proposal, recorded vote, attributed public statement | Supported account of the stated considerations and evidence limits |

A post-vote explanation can supervise the second task, but cannot be a feature in the first. A pre-vote statement explicitly announcing the vote is admissible for an announcement-reading task; report it separately from prediction without an announced intention. Actual public explanations are not recordings of private deliberation. Teacher-generated explanations must remain synthetic and cannot establish causal motives.

**Direct diplomatic precedents.** Liang et al., **UNBench** (AAAI 2026; preprint 2025), connects drafts, voting, and statements, with tasks for co-penholder judgment, representative votes, adoption, and statement generation. Use its task decomposition and matched proposal/outcome structure. Our acquired sample is not the entire benchmark. [Paper](https://arxiv.org/abs/2502.14122).

Nangia et al., **UNSC-Bench** (MME 2026), evaluates 26 LLMs on 469 resolutions with P5 roles and four languages. Its high-yes tendency and language effects motivate minority-class and multilingual diagnostics. It is a benchmark, not evidence for a winning fine-tuning objective. [Paper](https://aclanthology.org/2026.mme-main.10/).

Bailey, Strezhnev and Voeten, **Estimating Dynamic State Preferences from United Nations Voting Data** (2017), supplies a political-science comparator: dynamic ordinal ideal points. Such models help test whether an LLM adds beyond voting regularities. For forecasting a new proposal, an ideal-point model also needs a way to estimate proposal parameters without using its held-out votes; retrospective latent-position fit is not that forecast. [Author page](https://www.antonstrezhnev.com/publication/2017-estimating-dynamic-state-preferences).

**Learning from mission statements and policy documents.**

There are four materially different routes:

| Route | Actual training signal | Recommendation here |
|---|---|---|
| Continued pretraining | Predict the next tokens of source documents | Optional later ablation for domain language/knowledge; weakly matched to policy application |
| Grounded SFT | Document + scenario → reviewed supported answer | Primary next training experiment |
| Context distillation / constitutional preferences | A document-conditioned teacher provides outputs or comparisons for a student | Test after establishing a reliable grounded teacher and evaluation |
| Constitutional classifier | Document/rules + proposed output → consistency categories | Useful independent verifier; does not itself train the generator to act |

For grounded SFT, **RAFT** (Zhang et al., 2024) is a close methodological fit: train with relevant and distracting documents so the model learns which evidence supports an answer. Adapt that principle to policy attribution, preserving source IDs and concise support. Our proposal does not reproduce RAFT's entire rationale-generating recipe. [Paper](https://arxiv.org/abs/2403.10131).

The practical pipeline is:

1. Assign source/event families to splits **before** generating derivatives.
2. Extract dated, attributed policy clauses with exact support spans, scope, exceptions, and authority. Distinguish goals, preferences, obligations, forecasts, factual claims, and explicit prohibitions.
3. Build scenarios that exercise each clause: direct application, exception, missing information, competing principles, attribution distractors, and a verified policy update.
4. Generate candidate answers with the document available. Review whether each conclusion follows; do not assign a determinate action where policy is underdetermined.
5. SFT on the accepted answer with completion-only loss. Include cases where a correct draft needs no correction.
6. Sample the resulting model's actual errors. Correct them, then compare additional correction-SFT against DPO using the same evidence and underlying cases.

The local Germany critical-inputs example already illustrates the right supervision. Its 2023 strategy source supports reducing critical dependencies while maintaining economic ties and climate cooperation. For a hypothetical single-supplier proposal, an appropriate target identifies concentration risk and diversification, while saying the source does not determine approval of the particular contract. “Ban all Chinese trade” is an overgeneralization; a precise invented sourcing cap is unsupported. This is policy application, not an observed German contract decision. See `data/prepared/country-knowledge-20260914/examples.jsonl`.

Represent a policy clause as something like:

```json
{
  "country": "DEU",
  "institution": "federal_government",
  "policy_date": "2023-07-13",
  "principle": "Reduce critical dependencies while preserving economic ties",
  "scope": "critical sectors",
  "strength": "stated_policy_preference",
  "specific_contract_threshold": null,
  "source_span_ids": ["verified-span-id"]
}
```

This schema is illustrative. Publication date and first available date must be verified separately. A principle's scope and strength matter as much as its wording. Do not convert “prioritize” into “always choose,” or resolve conflicts by inventing a hierarchy absent from the source.

**How constitutional methods fit.**

**Constitutional AI** (Bai et al., 2022) uses principles to guide critiques and revisions for SFT, then AI preference judgments to train a preference model and perform RL. The transferable idea is turning prose rules into behavioral supervision. Replacing the RL phase with DPO is a practical adaptation, not an exact reproduction. [Paper](https://arxiv.org/abs/2212.08073).

**Constitutional Classifiers** (Sharma et al., 2025) uses natural-language rules to generate synthetic permitted/restricted examples and train safeguards. Our adaptation would classify whether an answer respects a dated policy packet. Use `supported`, `contradicted`, and `not_established`, potentially per claim, plus attribution and scope checks. This is proposed diplomatic supervision; their safety results do not validate these labels in our domain. [Paper](https://arxiv.org/abs/2501.18837).

**Constitutional Classifiers++** (Cunningham et al., 2026) adds full-exchange context, a classifier cascade, and efficient probes. Full context is particularly relevant when a statement is correct for one country or date but not another. Its production efficiency findings concern safeguards, not vote prediction. [Paper](https://arxiv.org/abs/2601.04603).

A verifier can filter synthetic data, rerank candidate outputs, or flag cases for review. If used as a reward, evaluate it on independently annotated held-out families first. Otherwise optimizing the generator may simply teach it to exploit the verifier. A consistency label must mean consistency with the supplied policy, not factual truth about every government assertion or endorsement of that policy.

**Open Character Training** (Maiya et al., 2025) is the closest persona-specific constitutional work. It uses constitution-conditioned teacher responses and unconditioned student responses for DPO, followed by synthetic introspective SFT; it studies 11 personas across three small open models. For us, dated institutional policy replaces personality traits. Do not inherit the assumption that every teacher response is preferable, or generate autobiographical “beliefs” for diplomats. [Paper](https://arxiv.org/html/2511.01689v1).

**Learning by Distilling Context** (Snell, Klein and Zhong, 2022) directly addresses internalization: a teacher sees helpful instructions/context; the student learns its final outputs without that extra context. Test this if you want stable institutional dispositions in weights. Keep a country/role identifier for a shared model, and retain changing facts in retrieval. Otherwise incompatible national policies would be distilled into an unidentifiable mixture. [Paper](https://arxiv.org/abs/2209.15189).

**On-Policy Context Distillation** (Ye et al., 2026 preprint) supervises student-generated trajectories against a context-conditioned teacher using reverse KL. It is a plausible later way to reduce the gap between teacher examples and student behavior; it requires teacher distributions and a sound teaching context. Its reported tasks do not establish diplomatic fidelity. Start with ordinary grounded SFT before this more involved comparison. [Paper](https://arxiv.org/abs/2602.12275).

**Where other disciplines help.**

| Literature | Transferable contribution | Boundary |
|---|---|---|
| Chalkidis et al., [Neural Legal Judgment Prediction](https://aclanthology.org/P19-1424/) (ACL 2019) | Facts-to-outcome prediction and structured decision labels | Published case descriptions may differ from information available to an actual decision-maker |
| Medvedeva and McBride, [Legal Judgment Prediction: If You Are Going to Do It, Do It Right](https://aclanthology.org/2023.nllp-1.9/) (2023) | Define a practically meaningful prediction task and inspect dataset construction | Predicting a published judgment is not automatically prospective legal reasoning |
| Hsieh et al., [Distilling Step-by-Step](https://aclanthology.org/2023.findings-acl.507/) (2023) | Rationale and label supervision as separate tasks | A generated diplomatic rationale is not expert ground truth; ablate its contribution |
| Park et al., [LLM Agents Grounded in Self-Reports](https://arxiv.org/abs/2411.10109v3) (2026 revision of 2024 work) | Rich qualitative evidence can support simulations without outcome-specific training | Individual interviews differ from strategic public institutional statements; useful grounding baseline |
| Abbeel and Ng, [Apprenticeship Learning via IRL](https://ai.stanford.edu/~ang/papers/icml04-apprentice.pdf) (2004) | Infer reward structure from demonstrated behavior under environment assumptions | Sparse votes and speeches do not identify hidden national utilities or transition dynamics |
| Ross et al., [DAgger](https://proceedings.mlr.press/v15/ross11a.html) (2011) | Collect expert corrections on states visited by the learner | Requires an expert/oracle able to label new states; static historical records cannot do this alone |
| FAIR Diplomacy Team, [CICERO](https://web.mit.edu/~gfarina/www/2022/cicero/) (Science 2022) | Couple strategic planning with language generation | Board-game rules, payoffs and trajectories differ substantially from real diplomacy |
| Wang et al., [SOTOPIA-π](https://aclanthology.org/2024.acl-long.698/) (ACL 2024) | Behavior cloning and filtered interactive learning | Its LLM-based social evaluation can overestimate trained agents; diplomatic scoring needs independent checks |

These are reasons to borrow experimental designs, not to combine every objective immediately. In particular, recovering “what diplomats truly want” via inverse RL is a much stronger identification claim than predicting their observed actions.

**Concrete next experiment.**

Keep the pinned Qwen3-8B non-thinking model and existing BF16 LoRA implementation for the first comparisons. First complete the documented stopping/decoding replay so repetition does not obscure supervision quality. Then prepare a new, reviewed release of policy applications and decision cases; do not silently promote the existing demonstrations into a clean test set.

| Arm | What is trained | What it answers |
|---|---|---|
| A | Nothing: base + dated evidence/brief | Is retrieval/prompting already sufficient? |
| B | Action-only SFT on expanded authentic decision cases | Does direct behavioral supervision improve observed-choice probabilities? |
| C | Same decisions plus grounded policy-application SFT | Does declared-policy supervision improve generalization beyond cases? |
| D, conditional | C plus correction-SFT versus C plus DPO on the same reviewed error cases | Do explicit preference comparisons outperform learning the corrected answer? |
| E, later | Distill the stable policy brief out of context | Can behavior persist with less policy context, and what accuracy/updateability is lost? |

For B/C, hold action examples and action exposure fixed and report extra auxiliary-token compute. Add an equal-compute B control if C helps. For D, both alternatives see the same cases and corrections; generated negatives need independent validation. Do not treat the workshop's ten authored pairs as sufficient for a preference-training conclusion. DPO optimizes pairwise preferences; it does not create their validity. [DPO paper](https://arxiv.org/abs/2305.18290).

Practical initial settings are the existing rank 16, alpha 32, dropout 0.05 and all-linear adapters, with one epoch and a **proposed** learning-rate comparison of `2e-5` versus existing `1e-4`. These are sensitivity points, not a literature-established optimum. Preserve completion masking and the Qwen non-thinking template. Run the smaller reviewed pilot before extending epochs; choose checkpoints using held-out behavior, not prose loss alone. Equalize country/event exposure and monitor answer-token shares. Keep separate task losses normalized so long policy text does not swamp actions. No universal mixture percentage or sample requirement is justified by the reviewed papers.

The first acquisition priority is more independent decision events with actual proposals and verified pre-decision packets, including minority actions and multiple issue families. The first annotation priority is expanding the policy-application examples into reviewed families with exceptions and underdetermined cases. Synthetic augmentation can diversify these families but cannot replace new historical choices.

**Evaluation that can distinguish progress from imitation of style.**

- Split by event, recurring proposal family, source document and all connected derivatives; add chronological and held-out-issue tests. Distinguish historical reconstruction from genuinely prospective collection because historical material may be in pretraining.
- For actions, report negative log-likelihood, Brier score, macro-F1, balanced accuracy, per-class recall and class frequencies. Include train-only country-majority, historical-neighbor, and simple text-classifier baselines. Bootstrap event/family groups rather than correlated country rows.
- The existing UPR majority baseline reaches roughly 69–85% raw accuracy across the displayed country/split combinations despite balanced accuracy of 0.5. Each evaluation split has only one country-review group. More recommendations from that review do not produce independent event-level validation. See [baseline report](../reports/decision_baselines.json).
- For policy applications, independently score source support, attribution, scope/exception preservation, unsupported commitments and useful uncertainty. Keep synthetically generated policy labels out of the authentic-vote score.
- Compare identical questions and evidence across country tags, including cases where countries agree. Use common-language tests and report original-language results separately.
- Test verified policy updates, irrelevant-pressure invariance, principle conflicts, and insufficient context. A hypothetical clause edit has a known gold action only when reviewed policy or expert annotation establishes it; otherwise score supported interpretation, not an invented counterfactual vote.
- Audit the automatic judge against blinded human reviews. Hold out whole policy/scenario families from teacher generation and judge calibration. Report disagreement rather than forcing uncertain cases into binary preferences.
- If negotiation is eventually trained, add on-policy trajectory evaluation; accurate one-step predictions under real histories do not establish behavior under the model's own previous actions.

The central empirical question is whether policy-application supervision improves held-out decisions and source-faithful behavior beyond the same evidence in a prompt. This is a stronger and more informative research claim than making country personas sound more distinct.
