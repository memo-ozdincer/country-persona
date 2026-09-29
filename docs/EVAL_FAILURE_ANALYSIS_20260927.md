# Why the first baseline failed

27 September 2026. Follow-up to the [30-output baseline](EVAL_BASELINE_RESULTS_20260927.md). **The observed failures combine incomplete decision evidence, strong sensitivity to prompt wording, and unsupported elaboration in source-based answers.** These experiments do not identify an internal value system or establish that persona fine-tuning is the remedy.

We ran **34 additional diagnostic generations** on the existing `def-zhijing` allocation: 24 initial interventions, then 10 adaptive follow-ups. Four original inputs were replayed exactly and reproduced identical output tokens and probabilities. All diagnostic inputs were retained in full; all outputs stopped at EOS. Cases were selected after seeing errors, so these are failure analyses, not a new benchmark score. The two tests containing the actual voting record are explicitly marked extraction controls and excluded from predictive conclusions.

## 1. A public stance is not a complete decision record

The model saw the draft and statements delivered three days before the Ukraine vote. Those statements establish policy positions but do not announce either India's or Brazil's eventual vote. The India policy answer itself correctly says the supplied speech does not establish a definite Y/N/A. Yet the separate forced-choice action answer selects No with 84.96% conditional probability. That is a discrepancy between source-sufficiency behavior and categorical prediction, not evidence that abstention means uncertainty.

The voting-day record helps explain the information gap:

- **Brazil:** rejected the referendums and upheld territorial integrity, while objecting to the draft's scope/language, limited contribution to de-escalation, short consultation time and negotiation process. It nevertheless chose **abstention**, not No. The earlier speech contains calls for dialogue but does not state these draft-specific procedural objections or announce that vote.
- **India:** reaffirmed sovereignty and international law, emphasized diplomacy and de-escalation, and described abstention in light of the evolving situation. Its public explanation does not supply a fully specified decision rule that lets us deduce the vote from the earlier speech.

Source: the previously acquired [S/PV.9143 bundle](../data/raw/eval-sources-20260927/record-9143-bundle.pdf), PDF pages 9 and 12 (meeting pages 5 and 8). Both full relevant pages were visually checked, with speaker boundaries preserved in the [extracted explanation receipt](../reports/eval-pilot-20260927/post-vote-explanations.json). These are public justifications, not independently established private causal motives. They were used for analysis; only the two explicitly marked extraction controls received an outcome quote.

**Implication:** a good training example needs the exact proposal, proposal-specific reservations, procedural context and information timing. “Supports sovereignty” or “wants negotiations” is not a sufficient mapping to a vote. Later explanations can be separate targets/analysis fields; they must not leak into a forecast's inputs.

## 2. The action interface is unstable

Each row below changes one prompt element from the evidence-conditioned baseline, except the explicitly combined full-name/natural-word condition. Text-label outputs are mapped to their stated meanings for this table; no Y/N/A probability is invented for a different output vocabulary.

| Prompt condition | India, Ukraine (actual A) | Brazil, Ukraine (actual A) | India, climate (actual N) | France, Ukraine (actual Y) |
|---|---|---|---|---|
| Original, replayed | N | N | N | Y |
| Full country names instead of ISO codes | Y | Y | Y | Y |
| Clarify that vote concerns adopting the draft | N | N | Y | Y |
| Remove the abstention-versus-uncertainty warning | N | N | N | Y |
| FAVOR / AGAINST / ABSTAIN | No | No | No | No |
| Yes / No / Abstain | No | No | No | No |
| Full names plus Yes / No / Abstain | No | No | No | No |
| Actual recorded abstention supplied: extraction control | A | A | — | — |

Three of four letter-label predictions flip when only the country headers are expanded. The earlier India/climate gain was already a Y/N logit tie; it disappears under the full-name and vote-target variants. France goes from a correct, 99.94%-conditional-probability Y to an incorrect No when the answer vocabulary changes. The natural-word follow-up shows this is not confined to the unusual all-caps vocabulary.

The model can emit and interpret A: explicit voting-record controls yield A for both actual abstentions, with conditional probability above 99.9999%. That establishes extraction ability on these controls, not successful forecasting. Removing the warning or clarifying the object of the vote does not fix either abstention error.

The tokenizations also differ: Y/N/A and Yes/No are single tokens, while Abstain is three; FAVOR/AGAINST/ABSTAIN use three/two/three. That limits probability comparisons between interfaces. It does not establish tokenization as the complete cause: country-name and explanatory-wording interventions also change predictions while keeping the original single-token labels.

**Implication:** we cannot yet interpret this evaluator's hard choices as stable national preferences. Keep country codes in metadata and test full names in prompts; predefine a small set of semantically equivalent formats, report sensitivity across them, and freeze the protocol before assessing training. Do not select whichever format happens to get these exposed cases right. A prompt change is an observed cause of the output change; its internal neural mechanism remains unknown.

## 3. Evidence helps factual fidelity but does not prevent added details

Without the dated speech, the original policy answers often substituted generic country-associated material for the actual statement: an Amazon-centered account for Brazil, generic capacity-building for India, and even the wrong UK position on the referendums. Those are failures to reconstruct a specific source, not direct measurements of the model's intrinsic political values.

With the speech, many required positions were recovered, but France's answer added financial and military assistance not specified in the selected passage and omitted its duration qualifier. This is consistent with background knowledge or generic completion filling gaps; the outputs alone cannot establish where the added details came from.

We appended the same claim-to-quotation instruction to four policy cases, also asking for explicit time qualifiers:

- **France/Ukraine:** the unsupported assistance types disappear and “for as long as is necessary” returns. All seven quoted spans match the supplied source. This is a promising local repair, selected after the error was known.
- **India/Ukraine:** the response still narrows “neighbours in the global South” to South Asia and omits the food/fuel/fertilizer detail. It supplies only one quotation, not support for every substantive claim.
- **Brazil/Ukraine:** the conditional-recognition answer remains broadly faithful, but supplies no exact quotations despite the new instruction.
- **India/climate:** source quotations support the central qualification and institutional argument. A quoted allegation from the question is correctly rejected; it must not be mistaken for a fabricated source quotation just because it is absent from the speech.

The [quotation check](../reports/eval-pilot-20260927/diagnostic-quotation-checks.json) checks literal spans, not entailment or complete claim coverage. Independent policy ratings remain pending.

**Implication:** include a quotation-grounded prompting baseline in the next comparison. For later SFT, useful targets are claim-to-source linkage, preservation of qualifications, and explicit limits on what the packet establishes. Adding citations or quotations by itself does not guarantee all claims are supported.

## What to change before training

1. **Separate three evaluations:** extracting a documented position; reconstructing/predicting a recorded action; and determining whether the supplied source establishes that action. Keep epistemic uncertainty separate from the institutional vote category A.
2. **Add invariance checks:** full-name/code variants, equivalent answer formats and a small number of neutral instruction paraphrases. Include clear positive controls and extraction controls. Report these separately from predictive scores and track probability support as well as hard labels.
3. **Broaden the decision evidence:** acquire draft-specific objections, negotiations and procedural context where available before the cutoff. Maintain later public explanations separately. Include abstentions and mixed positions across additional event families rather than treating every reservation as No.
4. **Calibrate the policy rubric:** use the existing fixture deck and actual-output packet with independent reviewers. Decide which missing qualifications are material before publishing an aggregate score.
5. **Then test one small behavioral SFT:** compare against the same evidence and a stronger source-grounded prompt. Training should improve supported decisions and faithful claims across held-out cases and prompt variants, not merely reproduce one brittle output format. Deliberation training remains later in the plan.

The next calibration checkpoint is therefore **evaluation robustness and source sufficiency**, ahead of a new training run. The original 4/7-to-5/7 result stays recorded, with this fragility attached. These diagnostics neither prove a universal anti-abstention bias nor validate a shared-value-substrate explanation.

## GPU and allocation checks

There is one allocated H100 80 GB under job **996664**, account **def-zhijing**, node **trig0042**. Before these diagnostics it was idle: 0% utilization, 0 MiB used, 41°C. During actual inference, three samples showed **58–59% utilization, 18,379 MiB used, 46–47°C, 206–212 W**, and zero reported volatile uncorrected ECC errors. The Python process was visible in the GPU process table. These samples support that the job actually exercised the GPU with substantial memory headroom; they are not a comprehensive hardware certification.

The two diagnostic runs generated 874 tokens from 83,189 prompt tokens in **22.51 seconds of model generation**, excluding loading, verification, tracing and retained idle time. Peak PyTorch allocated memory was **16.49 GiB**; `nvidia-smi` includes additional reserved/runtime memory. No output was cut off and no GPU-memory failure occurred. The reservation is intentionally retained with `sleep infinity` until **28 September at 01:30:55 EDT**; verify its current state before reuse.

Reproducible evidence: [frozen diagnostic inputs v1](../data/prepared/eval-pilot-20260927/failure-diagnostics-v1/manifest.json), [adaptive follow-up v2](../data/prepared/eval-pilot-20260927/failure-diagnostics-v2/manifest.json), [all results and hashes](../reports/eval-pilot-20260927/failure-analysis.json), [GPU load samples](../reports/eval-pilot-20260927/gpu-health-diagnostics-load.txt), and [retained allocation instructions](TRILLIUM_WORKFLOW.md).
