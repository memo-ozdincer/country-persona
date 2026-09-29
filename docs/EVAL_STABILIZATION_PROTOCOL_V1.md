# Evaluation stabilization protocol v1

Frozen before this experiment's inference, 27 September 2026. This is an exposed-development protocol, not a preregistered confirmatory benchmark. The two events and their earlier failures have already been inspected. Preserve this file after freezing; record results and amendments separately. Training is deferred while evaluation is stabilized.

## What the literature changes in our implementation

- UNBench v2, §5: use class-sensitive action metrics and chronological splits. Its statement similarity metrics do not establish that individual policy claims are supported. Our implementation retains macro-F1 and balanced accuracy, with explicit minority-class recall. [Paper](https://arxiv.org/abs/2502.14122v2).
- Centaur, Methods: predict held-out observed responses and score response likelihood; test unfamiliar settings. Our adaptation uses institutional actions, with event families as the independent unit. It does not turn synthetic prompt variants into independent observations. [Paper](https://www.nature.com/articles/s41586-025-09215-4).
- UNSC-Bench, §4.3: report per-class performance as well as macro-F1, since frequent Yes votes can hide failures. Consistency must be read alongside correctness. [Paper](https://aclanthology.org/2026.mme-main.10/).
- Wang et al. (ACL Findings 2024): first-token rankings can disagree with generated answers. Preserve both, plus invalid-output rate and legal-label probability mass. Our exact single-token interface makes the measured quantity explicit; it is not a probability of every semantically equivalent completion. [Paper](https://aclanthology.org/2024.findings-acl.441/).
- Pezeshkpour and Hruschka (NAACL Findings 2024): answer order can change MCQ results. Test all six mappings of the three outcomes to digits, with equal weight, and report dispersion as well as averages. [Paper](https://aclanthology.org/2024.findings-naacl.130/).
- Zhao et al. (ICML 2021): content-free calibration can reduce prompt biases in their few-shot settings. We do not assume a content-free diplomatic prior is valid or fit a correction to these seven labels. Such calibration remains a separately versioned experiment. [Paper](https://proceedings.mlr.press/v139/zhao21c.html).

## Experiment fixed before seeing these outputs

Use the pinned Qwen3-8B base model, BF16, SDPA, non-thinking chat template, seed 0 and the audited raw greedy runner. No adapters or optimization. Reuse the retained def-zhijing allocation. Keep complete inputs; context budget 8192, output cap 16 for these digit-only responses. A capped or malformed response is an error, not silently repaired.

1. Replay all 14 original action prompts (A: role + draft; B: same + dated statement).
2. For each, run all six mappings of Yes/No/Abstain to single-token digits 1/2/3. Run both ISO and full country-name forms: 168 prompts. The option text and system template are otherwise fixed. These forms test a specified interface family, not every possible paraphrase.
3. Add 18 clearly fictional extraction controls: three explicit recorded outcomes × six mappings. Keep these separate from historical results. These controls contain their answer by design; they test whether the interface can extract a known outcome.

There are 200 prompts but only seven historical decisions in two event families. Neither more permutations nor A/B pairing increases the independent sample size. Gold references are not needed or staged for inference. Cases, templates, mapping, model revision and this protocol are hashed before the run.

## Scoring contract

- For each prompt, record the full greedy completion, strict parsed semantic vote, and raw first-completion logits for the three declared single-token digits. Verify tokenization at the completion boundary. Map probabilities back to Y/N/A before scoring. Keep raw legal-label mass separately from the conditional distribution.
- Conditional NLL and multiclass Brier measure prediction within this fixed three-choice interface. They are not unconditional probabilities of a real country action, nor full-sequence likelihoods. Record generated-answer versus conditional-argmax agreement; neither substitutes for the other.
- For each parent and country-name form, average the six semantic probability vectors. Report NLL/Brier/accuracy of that equally weighted mixture AND the mean loss and accuracy over individual prompts. The mixture is an ensemble estimator, not evidence that the underlying model is stable.
- Report per-parent generated votes, all-six agreement, correct-under-every-mapping rate, pairwise disagreement, generalized Jensen–Shannon divergence (natural-log units), legal-mass range, and gold-probability range. Exact maximum-probability ties are unresolved, never broken by label order.
- Compare ISO versus full-name mixtures and paired A versus B. Report exact counts and case tables; do not produce confidence intervals or significance claims from these two development families. Preserve original Y/N/A results as a separate interface baseline; do not replace them with a better-scoring prompt.

## Separate source support from observed action

Record two distinct annotations: (1) the observed historical vote from the vote record; (2) what the admissible packet explicitly establishes. A prior statement may establish a policy position or announced draft support without establishing the later recorded outcome. Policy context alone does not entail a specific vote. Predictive uncertainty does not mean the country abstained.

Source-only extraction questions must allow “not established by this packet.” Outcome prediction remains a separate three-class task. Their scoring and denominators must never be mixed. An announced-position subgroup is reported separately from cases requiring inference. Historical reconstruction is the present claim: archival availability before the vote is still unverified.

## Policy rubric stabilization

Keep v1 criteria and old results immutable. Prepare an atomic v2 review specification with source spans, acceptable paraphrases, material qualifiers, counterexamples and explicit conjunction/alternative rules. Distinguish required-content omissions from unsupported additions and wrong attribution/time. Exact quote matching checks provenance only; it does not prove entailment or that all claims are covered. Empty answers cannot pass on the absence of hallucinations.

Use the 19 authored examples only to test scorer/rubric behavior. Use blinded actual model outputs for independent review. Report required-content coverage, unsupported-claim rate where claim annotation is complete, strict response pass rate, unratable fraction and reviewer disagreement separately. Do not invent human ratings or treat assistant labels as independent validation.

## Gates and useful next checkpoints

1. **Engineering gate:** strict mapping/hash checks, controlled-logit tests, original-prompt replay, complete token traces and synthetic extraction controls. A failed control must be investigated before attributing changes to persona training.
2. **Measurement gate:** publish the complete sensitivity table, even if the model remains unstable. Freeze an evaluation that exposes instability rather than claiming averaging has removed it.
3. **Construct gate:** finish packet-support annotations and independent rubric/source review; report agreement and adjudicate material disagreements. Authored fixtures alone do not satisfy this gate.
4. **Generalization gate:** add independent event families, audit related documents/translations before chronological splitting, freeze final test before training-data/model selection. The exposed two-event slice remains development-only.
5. **Training gate:** only then run a small shared evidence-conditioned LoRA and compare C to B on identical packets and interfaces. Broad persona/deliberation claims require independent-family evidence and subsequent matched-budget interaction tests.

No fixed persona-quality pass threshold is inferred from this tiny pilot. Practical improvement and noninferiority margins must be declared for the expanded development design before final-test inspection. A repeatable scoring pipeline can reveal an unstable model; those are different conclusions.
