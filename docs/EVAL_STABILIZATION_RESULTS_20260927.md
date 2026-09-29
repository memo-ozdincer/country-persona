# Evaluation stabilization: a repeatable evaluator exposes an unstable model

27 September 2026. No training ran. The user's decision to stabilize evaluation first is now the active gate. The [protocol](EVAL_STABILIZATION_PROTOCOL_V1.md) was hashed before the new inference run; all original results remain available. This checkpoint combines a counterbalanced action experiment, a revised policy review packet, and explicit source-support checks.

## Main finding

Counterbalancing did **not** solve the model's decision problem. Averaging all six answer mappings produced **Abstain for every historical decision**, in both evidence arms and both country-name forms: 2/7 correct. The original letter interface gave 4/7 without evidence and 5/7 with evidence. All 14 original prompts replayed with identical input tokens, output tokens and probabilities in the updated runner.

The 18 fictional extraction controls passed every mapping, and all 200 outputs were valid and stopped cleanly. Thus the new result is not explained by an observed parser failure, missing class mapping, malformed output or changed original-prompt decoding. The model can extract explicit outcomes in these simple controls while failing the historical prediction task. Those controls do not validate historical reasoning.

The new template changes answer symbols and explanatory wording as well as option placement. Differences between the old and new interfaces do not isolate a single causal mechanism. Variation within each six-member group isolates the declared choice permutation with the rest held fixed. No result here establishes the model's internal values or the country's private motives.

## Complete experiment

- 14 unchanged action-prompt replays.
- 168 historical variants: seven decisions × two evidence arms × two country-name forms × six mappings.
- 18 fictional extraction controls: explicit Yes/No/Abstain outcomes × six mappings.
- Still only **seven decisions in two exposed event families**, not 200 independent benchmark observations.

| Arm and country form | Mixture correct | Mixture NLL | Mean single-prompt accuracy | Same vote in all six mappings | Correct in all six |
|---|---:|---:|---:|---:|---:|
| A, ISO | 2/7 | 1.9133 | 40.5% | 4/7 | 2/7 |
| A, full name | 2/7 | 1.6706 | 45.2% | 3/7 | 2/7 |
| B, ISO | 2/7 | 1.6188 | 35.7% | 4/7 | 2/7 |
| B, full name | 2/7 | 1.4095 | 42.9% | 4/7 | 2/7 |

A supplies role/date/draft; B adds the frozen dated statement. The mixture averages semantic Y/N/A probabilities after mapping each digit back to its meaning. Mixture NLL is the loss of that ensemble, not the average individual-prompt loss; both are stored in the report. Lower NLL does not establish calibration or correct top-choice behavior. The model is confidently wrong on the climate India No case under this interface.

All 14 ISO/full-name mixtures agree, but every mixture says Abstain. This is a direct demonstration that consistency alone is an inadequate persona metric. Within individual prompt groups, answer order still changes some outputs. The complete case-level votes, JSD, probability ranges, legal mass, NLL/Brier and class metrics are in [the machine-readable report](../reports/eval-pilot-20260927/stability-v1-results.json).

The minimum raw probability mass on valid digit choices was 0.99962698. There were zero format errors, output caps or generated thinking markers. Probabilities remain first-completion-token probabilities conditional on the declared single-token choices; they are not full-sequence likelihoods or an unconditional probability of a real-world action.

Four historical variants have exact tied conditional maxima, treated as unresolved rankings rather than broken by label order. These explain the report's 41/42 generation-versus-argmax agreement in each stratum. There are zero disagreements where the conditional maximum is unique. The [validation receipt](../reports/eval-pilot-20260927/stability-v1-validation.json) lists the ties and verifies the executed source files against the staged payload.

## What changed in the evaluator

1. **Explicit semantic mapping.** Cases can declare distinct single-token output symbols, with boundary tokenization checks. Scores map them back to historical votes and reject mapping/hash mismatches. Original Y/N/A cases retain their behavior.
2. **A complete robustness report.** Missing/duplicated permutations fail visibly. Equal-weight mixtures are accompanied by individual prompt performance, all-six agreement, correctness under every mapping, JSD and country-name comparisons. Invalid answers and exact probability ties cannot become successful agreement through a default label.
3. **Version-bound policy ratings.** The proposed atomic rubric separates compound omissions, preserves duration/scope qualifiers, and adds a check for unsupported substantive assertions. Ratings bind to the rubric criteria/check hash as well as case and output hashes. Changed criteria require fresh ratings.
4. **Distinct source-support judgments.** Fourteen annotations distinguish prior policy context, explicit draft support and no supplied dated speech. Sixteen proposed source-entailment items distinguish supported, contradicted and not established. A prior announcement and a later observed vote are different facts; uncertainty is not an abstention vote.
5. **Reviewer disagreement tooling.** A comparison script reports content/check agreement, Cohen's kappa where defined, ratable coverage and exact disagreements for adjudication. Missing or unratable judgments cannot inflate agreement. Human identity labels alone do not prove independence.

The active policy draft is [construct-v2.1](../data/review/eval-pilot-20260927/construct-v2.1/manifest.json), which supersedes the initial construct-v2 draft by retaining the original resilience and existing-finance-commitment requirements during splitting. It contains 49 required units across eight questions, repeated over the paired 16 outputs. These are not 49 independent observations. The v1 rubric is unchanged; v1/v2 criterion averages use different denominators and must not be compared directly.

The [reviewer kit](../data/review/eval-pilot-20260927/reviewer-kit-v2.zip) contains the model/arm-hidden response deck, a source-support deck and blank rating files, without proposed answer labels. Wording may still reveal source access. All 16 policy responses remain **unresolved**, with no reported policy pass rate or human agreement. Assistant-proposed reference labels are not independent validation.

## Research basis

The protocol connects each implementation choice to a source: [UNBench v2](https://arxiv.org/abs/2502.14122v2) for linked institutional tasks and class-sensitive metrics; [Centaur](https://www.nature.com/articles/s41586-025-09215-4) for observed-response likelihood and generalization tests; [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) for per-class diplomatic evaluation; [first-token versus text-answer mismatch](https://aclanthology.org/2024.findings-acl.441/) and [option-order sensitivity](https://aclanthology.org/2024.findings-naacl.130/) for the interface diagnostics. The equal-weight six-mapping protocol is our specified diagnostic, not a validated diplomatic debiasing algorithm. Content-free calibration remains a separate hypothesis, not an automatic correction.

## Verification and compute

The action/inference/source/policy suite passed 65 tests after these changes; three additional reviewer-agreement tests passed. Structural validation checked 146 source-span occurrences, all 16 rubric hashes, and the absence of fabricated ratings. The original 14-action replay and 18-control extraction results provide model-level checks alongside the CPU tests. The authored checks test behavior of the evaluator, not its external validity.

The 200-case Qwen3-8B base run used 474,264 prompt tokens and generated 400 tokens, with 22.48 seconds of measured generation and a peak 16.49 GiB of torch-allocated GPU memory. The experiment helper completed in 55 seconds, including setup; retained-allocation billing is separate from measured generation time. Weight bytes were reverified against the pinned snapshot receipt. The model and source hashes are in [the run receipt](../runs/stability-996664-v1/run.json).

Job 996664 on `def-zhijing`, node `trig0042`, remains retained with `sleep infinity`, subject to its existing 01:30:55 Toronto-time expiry on 28 September. At 23:31:48 on 27 September, the H100 was idle, at 42°C, with 0 MiB process memory and zero reported volatile uncorrected ECC errors. No new allocation or training job was submitted for this checkpoint.

## Next gates

- **Complete:** repeatable traced scoring, strict mappings, original-output replay, counterbalanced reporting and versioned review tooling.
- **Measured failure, not solved:** stable/correct historical predictions across answer interfaces. Do not pick the best of the exposed prompts or call ensemble agreement a fix.
- **Pending independent review:** semantic source labels, materiality of rubric requirements and reviewer agreement. Review the packet separately, then adjudicate ambiguity before selecting a model by these scores.
- **Pending independent cases:** expand beyond these two exposed families, audit exact decision stages/source cutoffs, and freeze separate development/final-test data. Archive timing remains unverified, so the present task is historical reconstruction.
- **Training stays deferred.** Once the construct and data gates are met, compare one small shared evidence-conditioned LoRA against the same-evidence base model across fixed interfaces. Keep action likelihood, grounded policy fidelity and robustness separate. Multi-agent deliberation remains a later matched-budget experiment.

Useful lesson from this checkpoint: a reproducible, perfectly parseable answer can still be consistently wrong. The evaluation now makes that failure visible instead of rewarding it as successful persona consistency.
