# Research goal, prompting concern and training method

27 September 2026. Clarification of the [research anchor](RESEARCH_ANCHOR.md) after the user's question about Utility Engineering, the Nature paper, constitutional training and the purpose of deliberation. Literature findings below are distinct from our proposed diplomatic adaptation. No additional model experiment is claimed.

## Application goal and testable research claim

The proposed application goal is to improve deliberation about international policy: represent documented institutional perspectives accurately, expose substantive conflicts and tradeoffs, and produce defensible options that address those constraints. Agreement alone is not success; a correct analysis may explain why agreement is unavailable.

The testable research question remains: **Does training on dated institutional behavior and policy application improve fidelity beyond the same model supplied with the same evidence, and does that improvement help collective analysis at a matched compute budget?**

Separate observed behavior, declared policy and deliberation quality. An institution can act inconsistently with its public principles; predicting that action and interpreting the principles are different tasks. The unit is country–institution–date, not a timeless national personality or a population's average beliefs. Historical imitation does not establish that the imitated decision was desirable.

## What the supplied literature supports

**Centaur / Nature:** fine-tuning Llama 3.1 70B on Psych-101 with QLoRA and response-only loss improves prediction of held-out human behavior; the paper also tests new task settings and autonomous simulations. This supports learning observed behavior from context. It is not constitutional training and does not establish diplomatic or multi-agent validity. [Paper](https://www.nature.com/articles/s41586-025-09215-4).

**Utility Engineering:** v1 reports convergence of elicited default preference profiles with model scale. Shared training data is a hypothesized cause, not an established mechanism. Appendix D.6 also demonstrates divergent prompted politician profiles. The paper therefore motivates testing homogenization rather than asserting that persona prompting cannot work. Its utility-control experiment trains against a simulated LLM citizen assembly; those targets are not measured public preferences. [Sections 6–7 and Appendix D](https://arxiv.org/pdf/2502.08640v1).

**RAFT:** training on questions with relevant and distracting documents improves domain question answering in the reported settings. Borrow evidence selection and grounded answers; validate the adaptation to institutional policy separately. [Paper](https://arxiv.org/abs/2403.10131v2).

**UNBench and UNSC-Bench:** provide diplomatic evaluation tasks and reveal limitations in default voting behavior and language stability. They do not establish that vote fidelity yields better deliberation. UNSC-Bench explicitly acknowledges limited prompting, missing diplomatic context and possible historical memorization. Our local audits additionally found release/scoring/label issues. [UNBench](https://arxiv.org/abs/2502.14122v2), [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/), [local learning log](EVAL_LEARNING_LOG_20260926.md).

**Legal Judgment Prediction:** provides the evaluation warning that an outcome-era account can contain information unavailable to a real forecaster. Preserve task-specific information cutoffs and keep subsequent explanations outside forecasting inputs. [Paper](https://aclanthology.org/2023.nllp-1.9/).

## Three different training ideas

| Method | Source of supervision | Role here |
|---|---|---|
| Behavioral SFT, inspired by Centaur | Context and actual recorded responses/actions | First method: teach observed institutional behavior |
| Grounded policy SFT, informed by RAFT | Dated evidence and reviewed applications of it | Same optimizer, separately tagged supervision; measure its incremental benefit |
| Constitutional/context-distillation methods | A principles-conditioned teacher generates revisions or preferences | Conditional later comparison for persistence and policy-consistency failures |

Original Constitutional AI uses principle-guided critique/revision SFT followed by preference-model-based RL from AI feedback. A policy brief alone is not that training algorithm. [Paper](https://arxiv.org/abs/2212.08073).

The existing training memo also identifies **Open Character Training**, a closer constitutional persona precedent. It uses constitution-conditioned teacher responses in DPO, then synthetic introspective SFT; its experiments report greater robustness than system prompts and activation steering for assistant personas. Its traits and evaluations differ from documented government policy. For our adaptation, a dated source-backed policy brief could guide examples and review, but teacher preferences require verification and synthetic self-descriptions are not evidence of institutional beliefs. [Paper](https://arxiv.org/html/2511.01689v1), [training memo](TRAINING_RESEARCH_20260923.md).

## Concrete first training experiment

Use one shared country/role-conditioned LoRA adapter on the pinned base model. Each input contains the country, institution, date, task/proposal and admissible evidence; each target is a recorded action or attributed substantive response. Mask loss on input/context tokens and learn only from target answers. Keep task sampling explicit so long speeches do not dominate short decisions.

Reviewed policy-application examples can add supported objections, conditions, exceptions and uncertainty. Keep authored supervision identifiable and test its contribution as a data ablation. Synthetic scenarios can exercise documented principles; they cannot create historical votes or unobserved motives. Keep changing facts in retrieval.

Compare the trained model to a strong same-evidence prompted baseline. A shared adapter may also homogenize behavior; changing weights is not evidence that we changed a latent value system. Only measured generalization and persistence justify the intervention. Add preference training after concrete errors establish what the preference labels should correct.

## Make the prompting concern measurable

Add **false consensus** as a proposed diagnostic: among country pairs with independently supported different positions on the same case, measure how often their model outputs incorrectly collapse to the same position, before and after discussion. Also measure fidelity on genuine agreement cases, so artificial disagreement is not rewarded. Test changes under irrelevant majority pressure separately from justified changes after new evidence.

This diagnostic complements action NLL, grounded policy fidelity and matched-budget deliberation gain. It is proposed here, not implemented or measured. A pairwise ranking elicitation is a behavioral probe, not identification of a government's private cardinal utility.

The immediate next deliverable remains the small reviewed action **and policy-application** A/B evaluation. Preserve prompting as an empirical control; do not assume its failure or commit to constitutional/DPO training before that comparison.
