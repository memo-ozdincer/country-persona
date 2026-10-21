# SFT trials: plain descriptions and exact evidence

[Start here](README.md) · [Generated model outputs](../evidence/README.md) · [Evaluation guide](../evidence/EVALUATION_GUIDE.md)

These are simple onboarding names for seven principal SFT trial families. A family can contain multiple separately inspected fits. They do **not** replace the historical run IDs or omit the unsuccessful objective/DPO branches: the [complete ledger](../../reports/CONSOLIDATED_RESULTS_20261019.json) accounts for all 42 nonzero Qwen3.5 runs/continuations. All seven families use Qwen3.5-4B with response-only LoRA SFT; the base weights are frozen.

## SFT Trial 1: Given points → complete memo

**Desc:** give the model checked points containing the countries' positions and the intended analytical content; teach it to write a complete memo from those points.

- **Context:** source identifiers and checked country-specific bullet plans. Full original speeches are retained for audit but are not the student's input in this trial.
- **Format:** ordinary chat instruction + supplied plan → a complete analyst memo with national positions, common ground, disagreements and proposals distinguished from official commitments.
- **Example answers:** two assistant-authored complete climate/Ukraine memos, 434 and 453 words. These are supervised targets, not authentic government speeches.
- **Training:** one fresh 20-update fit on the two examples. The separate South Sudan monitor was excluded from fitting but had already been inspected.
- **Eval/result:** base and adapter each answered three identical plans. Both already corrected the main stance/false-consensus errors. SFT removed invented memo-writing dates in 3/3 and repaired selected details, while introducing/retaining omissions. Given a decision, better writing does not prove the model learned to choose that decision.
- **Read:** [targets](../../configs/posttraining/qwen35-plan-to-text-targets-20260930.json), [supplied plans](../../configs/posttraining/qwen35-plan-to-text-content-20260930-v2.json), [fit config](../../configs/posttraining/qwen35-plan-to-text-fit-20260930.json), [full report](../AURORA_QWEN35_PLAN_TO_TEXT_20260930.md). Original transcripts/adapter: snapshot-v47.

## SFT Trial 2: Full country statements + changed proposal → short country response

**Desc:** give both countries' complete statements and a hypothetical proposal; teach a short response that preserves the assigned country's position, notices repairs and avoids invented commitments.

- **Context:** complete India/Brazil statements from the 9 December 2022 sanctions meeting, plus a pressure/repair/attribution/shutdown scenario. No private plan or completed decision is supplied in the training prompt.
- **Format:** system instruction + assigned delegation + scenario + both full statements → one short complete response, requested at 80–120 words.
- **Example answers:** four source-checked assistant-authored targets; later four more attribution/shutdown contrasts. [All eight full conversations](../evidence/minimal-country-sft-20261021/training.md).
- **Training:** three separate fresh fits: four examples/16 updates; four examples/64 updates; eight examples/64 updates. The eight-example fit took 94.19 seconds. These are not one 144-step model.
- **Eval/result:** eight new-wording, same-source cases: base 23/40 content checks, four-example fit 34/40, eight-example fit 38/40. Application/commitment: 7/16 → 15/16 → 15/16. Four examples delivered most application gains; eight recovered coverage/attribution and traded one correction for a qualified partial-state regression.
- **Read:** **[actual generated replies](../evidence/minimal-country-sft-20261021/model-outputs.md)**, [all inputs/grades](../evidence/minimal-country-sft-20261021/comparison.md), [training metrics](../evidence/minimal-country-sft-20261021/training-metrics.md), [configuration](../../configs/posttraining/qwen35-minimal-country-extension-20261005-v1.json). Full historical adapters: snapshot-v47.

## SFT Trial 3: Paired proposal states → repair only what remains wrong

**Desc:** provide the source and a proposal that may already contain repairs; teach complete answers that preserve existing repairs and change only the remaining defects.

- **Context:** dated country evidence and explicitly described hypothetical proposal states. The Brazilian pair changes whether a universal delivery gate still exists, while retaining the other source/authority requirements.
- **Format:** native chat → a complete response under a 90-word/two-section contract. Recommendations, source claims, costs and unknown official endorsement/future votes must remain distinct.
- **Example answers:** eight preferred complete targets spanning the four-country application component. One 88-word repaired-gate counterpart is added while seven older targets/inputs remain unchanged. Negative answers are diagnostic only; they receive no preference gradient in this fit.
- **Training:** one fresh chosen-only 256-update fit, 32 presentations per target. This final comparison adds both data and compute; it does not isolate a data-only effect.
- **Eval/result:** two excluded Brazilian state combinations and one UK case strictly pass. Both Brazil cases retain correct Court attribution and distinguish whether the gate remains. A second UK case and an authenticated hypothetical Indian update remain ambiguous. Same-source development, not sealed OOD or broad negotiation ability.
- **Read:** [full report](../AURORA_PAIRED_BRAZIL_APPLICATION_20261007.md), [config](../../configs/posttraining/qwen35-paired-brazil-application-fit-20261007-v1.json), [stored-evidence receipt](../../reports/paired-brazil-application-checkpoint-20261007-v1.json). Data, original outputs and adapter: snapshot-v47.

## SFT Trial 4: Meeting scenario + earlier talks + delegation → authentic speech

**Desc:** give the meeting agenda/scenario, actual earlier turns in chronological order and the requested country/role; train the model to produce that delegation's authentic next speech.

- **Context:** sanctions and climate records; UK and India. Full earlier history fits for sanctions. For longer climate/Ukraine records, the fixed prompt budget retains only the immediately preceding complete speech plus scenario metadata. It is not a full-history experiment on every meeting.
- **Format:** readable scenario/country/role markers in a causal sequence → the complete authentic speech plus the existing record-end token. Earlier context and the target header are masked from direct loss. Learned atomic country tokens were not trained.
- **Example answers:** four actual UK/India speeches, normalized against the primary PDFs. These are authentic public institutional statements, not assistant-written policy answers.
- **Training:** one fresh 128-update fit, 32 presentations per speech.
- **Eval/result:** all four fitting speeches exact, 20/20 fitting units. Both Ukraine development cases fail in raw and corrected-native formats, with worse reference likelihood and invented material. Missing input facts qualify reconstruction failures; invented policies and extra speakers remain errors. Do not scale this failed-transfer branch.
- **Read:** [all four complete SFT sequences](../evidence/meeting-context-20261021/training.md), **[actual generated replies](../evidence/meeting-context-20261021/model-outputs.md)**, [config](../../research/scenario-role-sft-20261017-v1/fit-config.json), [full report](../SCENARIO_ROLE_CHECKPOINT_20261018.md). Adapter: meeting-context private release; bounded data/outputs are tracked.

## SFT Trial 5: Checked source points → source-faithful speech

**Desc:** give complete grounded source content/points in native chat; teach a complete short speech that preserves who said what and its qualifications.

- **Context:** UK/India sanctions and climate source targets, with attributed content supplied. This is a writer task, not discovery of hidden national preferences.
- **Format:** the model's native system/user/assistant template → a complete source-only public statement. Source-only scope excludes new proposal analysis.
- **Example answers/training:** four complete source-conditioned targets; one fresh 32-update fit. [Exact inputs/targets and split labels](../../research/native-plan-writer-20261019-v1/examples.json).
- **Eval/result:** excluded women, peace and security source cases improve from base 14/18 to 18/18 and 0/2 to 2/2 strict. Full application remains unreliable. A conflicting no-analysis instruction in the original application prompt was separately corrected; that prompt repair is not a training gain.
- **Read:** [config](../../research/native-plan-writer-20261019-v1/config.json), [report](../NATIVE_PLAN_WRITER_CHECKPOINT_20261019.md), [adapter manifest](../../reports/native-plan-writer-adapter-manifest-20261019-v1.json). Onboarding alias: the historical `native32` branch.

## SFT Trial 6: Source points + proposal → source summary and application

**Desc:** retain the four source-writing examples and add one complete example that applies the supplied content to a hypothetical proposal.

- **Context/format:** native chat with attributed source points and current proposal → a complete labeled source/application response with authority boundaries. Supplied facts and decision guidance remain part of the task.
- **Example answers/training:** five complete targets; one fresh 40-update fit, not a continuation of Trial 5. [Exact examples](../../research/native-application-writer-20261019-v1/examples.json).
- **Eval/result:** WPS source retention remains 18/18. Full WPS application covers 24/24 material checks but only 1/2 strict: France is 243 words against a 240-word cap. Full Brazil improves from base 7 met/5 unmet/1 uncertain to 10 met/1 unmet/2 uncertain of 13, without a full pass. Common-draft revision repairs none of the seed failures.
- **Read:** [config](../../research/native-application-writer-20261019-v1/config.json), [report](../NATIVE_APPLICATION_WRITER_CHECKPOINT_20261019.md), [adapter manifest](../../reports/native-application-writer-adapter-manifest-20261019-v1.json). Historical name: `native40`.

## SFT Trial 7: Add an application-only partial-state example

**Desc:** keep the previous five examples and add one short example that performs only the requested proposal update, preserving already-correct state and clear ownership.

- **Context/format:** attributed source/proposal state in native chat → an application-only response; the added target has 81 words. Five older targets remain byte-identical.
- **Example answers/training:** six targets; one fresh 48-update fit, not a continuation of Trial 6. [Exact examples](../../research/native-scope-partial-writer-20261019-v1/examples.json).
- **Eval/result:** application-only scope 0/3 → 3/3; WPS source 18/18 and Brazil source 9/9 retained. But full Brazil regresses from Trial 6's 10 met to 8 met of 13, and state/authority ambiguities remain. A separate unedited source-plus-companion composition reaches 13/13 material checks in 233 words but misses a required heading. Do not call this a general upgrade.
- **Read:** [config](../../research/native-scope-partial-writer-20261019-v1/config.json), [report](../NATIVE_SCOPE_PARTIAL_CHECKPOINT_20261019.md), [adapter manifest](../../reports/native-scope-partial-adapter-manifest-20261019-v1.json). Historical name: `native48`.

## Reference trial: published persistent-character reproduction

**Desc:** reproduce the released humorous-persona recipe/data on a separate Qwen2.5-7B model: preference training (DPO + chosen NLL + approximate KL), then introspective SFT.

212 preference updates + 370 SFT updates = 582, separate from the 4,182 Qwen3.5 updates. Humor recognition rises 10.4% → 58.6%; strongest neutrality condition 4.2% → 35.2%. Evaluator overlap, factual errors and one-persona scope limit the finding. This is our strongest persistent-style result; it is not a country-policy benchmark. [Full reproduction](../OPEN_CHARACTER_REPRODUCTION_20261004.md).

## Evaluation-only follow-ups

- **Context attribution/read–write decomposition:** supplied earlier country evidence → owned quote cards → actual model-produced fact map → public statement. No optimization. Coverage 12/18 → 15/18 → 18/18; only one provisional strict pass. [Actual outputs](../evidence/meeting-context-20261021/model-outputs.md#context-follow-up-11-generated-outputs).
- **Multi-agent revision/aggregation:** measured peer/self-revision and synthesis controls. No demonstrated peer advantage; false consensus, omitted constraints and unsupported peer claims remain. [Latest interaction report](../AURORA_SANCTIONS_INTERACTION_20261007.md).
- **Next proposed evaluation:** role-only source-based recommendations without a supplied action rule. Design only, unrun. [Next steps](NEXT_STEPS.md).

Independent semantic review is still needed. A software pass, a lower fitting loss or exact training recall is not a generalization result.
