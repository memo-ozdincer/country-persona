# Separating quote verification from entailment

A role model quoted a mandate that permitted either sequence and used it to justify parallel-only sequencing. A different reply cited simulated package text in place of the private mandate. Those errors require separate checks. Validate exact source attribution mechanically. Then measure whether the source supports the candidate claim, including scope and authority.

ALCE evaluates citation quality alongside correctness and fluency. JudgeBench uses objectively keyed response pairs to test whether a judge can identify a correct answer. TRUE compares factual-consistency evaluations across datasets. For the UN benchmark we keep claim accuracy, quote attribution, and the judge's classification behavior separately visible. [ALCE](https://aclanthology.org/2023.emnlp-main.398/) · [JudgeBench](https://arxiv.org/abs/2410.12784) · [TRUE](https://aclanthology.org/2022.naacl-main.287/)

The diagnostic panel contains eight pairs. Each pair has an entailed claim and an unsupported or contradicted foil anchored to the exact same quote. Examples cover private mandates, vote and procedural authority, and the public workshop ledger. Four additional false quotes are checked mechanically and never sent to the model. The model sees the quote, the full source block and one claim at a time, with no gold label. Response code meanings are reversed in a second call. The experiment records A/B conditional logit preferences and abstains if the decoded verdict changes across the two code assignments. This diagnostic isolates the judging decision from open-text output formatting.

## Binary diagnostic

Frozen Qwen3.5-4B accepted 5 of 16 supported calls and rejected all 16 unsupported calls. Requiring both code orders to agree produced 9 stable correct answers, 4 stable wrong ones and 3 abstentions across the 16 distinct claims. Both claims were stably correct in only one of eight minimal pairs. The four invalid quotes were rejected before using the model.

Averaging the two signed logit margins still gave only 9/16 correct absolute labels. For each pair, however, the supported claim's averaged margin exceeded its same-quote foil's margin. That relative ranking was correct for all eight pairs. Keep this distinction in the reward design. A standalone accept/reject gate would discard many valid claims. Relative ranking instead assumes explicitly competing claims and cannot establish that the higher-ranked claim is valid on its own. [Binary metrics](diagnostic-evidence/metrics.json) · [Margins](diagnostic-evidence/margins.json) · [Token replay](diagnostic-evidence/replay.json)

The reserve panel was written and hashed before the diagnostic run completed. All its claims use new authored phrasing. It tests the same binary procedure plus a direct side-by-side comparison under both claim orders. The reserve panel is a contrastive test of the benchmark rubric, with no independent labels and no assertion of country or source-family generalization. [Reserve panel](reserve.json)

## Reserve comparison

| Evaluation on new wording | Correct |
|---|---:|
| Supported claims accepted, per code order | 6/16 |
| Unsupported claims rejected, per code order | 14/16 |
| Absolute labels from averaged margins | 9/16 |
| Supported claim ranked above its foil using averaged margins | 8/8 pairs |
| Direct claim comparison correct in both orders | 8/8 pairs |

Six of 16 distinct claims receive a stable correct absolute label. The direct comparison makes the correct choice on all 16 ordered prompts, with no order reversals. The two invalid quotes fail containment. These results support testing direct comparison when the task supplies mutually exclusive alternatives whose truth is determined by the card and package. They give no evidence that the same method can establish support for arbitrary text or handle a candidate set with no correct answer. [New-wording results](reserve-evidence/metrics.json) · [Reserve token replay](reserve-evidence/replay.json)

## Application to disputed workshop options

Use the direct comparison procedure for the five options disputed by the two role-menu extraction methods. Each prompt contains the role's prose mandate and one offered package. Its two mutually exclusive candidate statements say the package either meets all requirements or fails at least one. Reverse the candidates and withhold a decision when the rankings disagree. Both prompts see the same card and package. The compiled menu is routed and verified with the same public ledger and authored scenario checks.

The model consistently accepted every package under review. The two disputed French packages are eligible, while all three disputed UK renewed-review packages are ineligible under the briefing-only instruction. Thus the model got only 2/5 role-package decisions right despite 5/5 agreement across orders. The output menus reproduce the direct-list baseline, with four of five exact. The learned sanctions gain remains 6/6 versus 4/6, and both arms certify 12/12 membership agreement presentations. The nine membership impasse presentations remain unresolved in both arms. Relative pair ranking on the quote rubric does not validate the same model's role-and-package decisions. Baseline and learned workshop rewards still depend on verified disclosures and the authors' scenario rules. [Package comparisons](application-evidence/predictions.jsonl) · [Downstream outcomes](application-evidence/metrics.json) · [Exact replay](application-evidence/replay.json)

## Task-matched package panel

Four new fictional private cards use the existing sanctions and membership package menus. Three specify two simultaneous conditions. The sanctions pair shares package F, while the membership cards have disjoint menus. Every role-package combination is evaluated, including straightforward options and options that satisfy only part of a mandate. The earlier quote panels score source entailment. This panel asks whether a concrete package satisfies a role's entire mandate. It shares historical context and option inventories with prior work.

The direct comparison uses the established A/B contrast with reversed claim order. A package judgment is admitted when both orders agree. A role with an abstention has no compiled menu for dispatch. The scoring code independently compares the inferred signs with the authored workshop reference before admitting them into the ledger. Both routing policies are evaluated on all four eligible opening pairs per family, first with authored menus and then with inferred menus. These eight opening pairs share the same four new model-input cards, so their outcomes are dependent. Public-historical prediction and final prose quality stay outside this package test. [Private cards and evaluator keys](package-cards.json) · [Runner](package_panel.py)

The direct comparison was correct on 3/8 eligible and 12/20 ineligible role-package items, wrong on one eligible item, and abstained on the other twelve items. All four role menus contained at least one abstention. None of the seven package pairs differing in exactly one field were both correct. In sanctions, the stable correct judgments contain no mutually accepted package even if a planner may pool every supported sign for free. In membership, those same individual judgments contain at least one correct exclusion per package, sufficient to prove an impasse in principle. [Raw judgments](package-evidence/predictions.jsonl) · [Menus and outcomes](package-evidence/metrics.json) · [Proof availability and one-field switches](package-evidence/availability.json)

### Retaining partial evidence

The original dispatch requires a complete menu and certifies neither scenario. In a post-hoc comparison, each actor can now keep its stable individual predictions. An unknown value is unavailable for disclosure. The simulated environment can reject a false predicted sign at submission time, after which that actor's sign is withdrawn. The rejection does not establish the opposite sign. Both original routing methods retain their usual choices when those choices are available and fall back to the remaining inferred signs otherwise.

Keeping partial signs alone did not recover either outcome. A separate deterministic rule gives priority to evidence that immediately verifies agreement or excludes a package. It keeps the floor with the current delegate while that delegate has another known exclusion. This recovers 4/4 membership impasses from the exact same model predictions and leaves sanctions at 0/4. All arms use the same seven continuation slots after the two opening opportunities, and no false claim enters the ledger. The original MARL policy was trained with complete local menus. The partial-evidence comparison does not establish a learned gain on that shifted input distribution. [Partial-evidence replay](package-evidence/partial-dispatch.json)

### Field-first interpretation and uncertainty

The same four cards were judged one field at a time under reversed answer order. This asks which value is required or whether the field is unconstrained, then compiles package signs. Eleven of twelve fields were exact in both orders and three of four menus were complete. Both routing policies recovered the four membership impasses. Brazil's sanctions reporting field changed from unrestricted to aggregate across answer orders. With a complete-menu gate, both policies still missed all four sanctions agreements. [Field test outputs](field-evidence/metrics.json) · [Token replay](field-evidence/replay.json)

Keeping the set of observed values for that field gave two candidate Brazil readings. Package F satisfies both. Package E satisfies only one and remains unknown. Across all cards, 27 package signs were invariant under the observed readings and matched the authored reference. No truth label was used to pick a reading. The reference still lets the simulated environment independently verify any signed disclosure.

| Model input and dispatch | Sanctions agreement /4 | Membership impasse /4 |
|---|---:|---:|
| Direct package comparison with complete-menu requirement | 0 | 0 |
| Field-first comparison with complete-menu requirement | 0 | 4 |
| Invariant signs with either existing partial dispatcher | 3 | 4 |
| Invariant signs and immediate handoff after a positive offer | 4 | 4 |

The third row leaves F unresolved on opening DE. Brazil offers F on continuation six, retains the floor and then passes. Immediate handoff lets India confirm F on continuation seven without adding a slot. Package E remains unresolved in the final record. Both the scripted and learned policies certify 4/4 agreements and 4/4 impasses under this treatment. The adaptive handoff rule was designed after observing the remaining DE miss. On the previously exposed complete-menu six-option grid it changes no certificate counts or aggregate turn costs for either policy. [Invariant-sign traces](field-evidence/invariant-dispatch.json) · [Handoff traces](field-evidence/handoff-dispatch.json) · [Complete-menu regression audit](field-evidence/handoff-grid-audit.json)

All 16 paired records render from public evidence and retain the historical-authority boundaries. The result is an end-to-end hybrid diagnostic with model-interpreted prose and exact simulation validation. It exercises new cards, two previously exposed historical families and an adaptive interface. It does not establish a learned advantage over the script on these openings or accuracy when the true mandate falls outside the model's observed readings. [Final records](field-evidence/final-records.json) · [Derived replay](field-evidence/derived-replay.json)
