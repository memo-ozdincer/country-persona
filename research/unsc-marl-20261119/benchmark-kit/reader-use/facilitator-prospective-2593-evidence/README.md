# Prospective Resolution 2593 routing test

The frozen routing policy sees a new meeting and resolution on an agenda used earlier in development. UNBench event 2397 occurs in its author-test release. UNSC-Bench adopted row 243 has the same meeting, draft, date and all 15 votes as the UN roll call. Card custody and communication loss are simulated. The underlying French, Chinese and Russian positions come from national explanations recorded after the vote. The reply cards give the model normalized paraphrases of those statements. [Benchmark joins](joins.json) · [Official meeting](https://docs.un.org/en/S/PV.8848?direct=true) · [Resolution](https://docs.un.org/en/S/RES/2593(2021)?direct=true)

The model sees three request topics and a silence control. Each cached reply sees one physical question or silence and a single authorized documentary card. The chair uses a fixed source-checked renderer. The final compares the two abstentions only when both national cards pass admission. It preserves the Council's separate demands, calls, expectations and requests. It contains no simulated change to the historical vote. [Frozen packet and criteria](packet.json) · [Protocol](protocol.md)

The two priors are exact distributions over all 64 inventory pairs and 16 link outcomes per pair. They reuse the same language generations. The initial and fitted rules, fixed request script, optimized independent team and exact public planner share their opening policies. The independent comparator has an optional third delivery without a chair request. Attempted messages are charged in every arm. The fixed-renderer full-source ceiling is 70 of 70.

## Results

Frozen Qwen3.5-4B decoded all four inputs correctly. All 12 replies finished within 52 words. Four passed the locked completeness and factuality gate. Those were the three question-free replies and the France reply to its matching question. The China reply to its matching question omitted necessity. The Russia reply to its matching question omitted the link between the sponsors' treatment of its proposals and its abstention. Five of six cross-delegation replies added an unsupported attribution or denial. In one such reply, Russia's source card became a claim that Paris abstained. The remaining cross-delegation reply correctly withheld Beijing's account and dropped France's UNAMA point. [Exact-span annotations](review.json) · [All 16 model outputs](final-records.json)

| Prior | Fitted, question visible | Initial, question visible | Fixed script, question visible | Independent | Fitted, source-only writing |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uniform | 53.269 | 54.417 | 53.437 | 56.456 | 56.838 |
| Correlated duplicates | 51.690 | 51.819 | 51.712 | 54.794 | 54.965 |

Values are expected final-record points out of 70. On the uniform prior, complete fitted records go from 1.25% to 14.58% in the source-only replay, compared with 12.53% for the independent team. Under correlated duplicates the corresponding rates are 1.07%, 11.57% and 10.65%. Approximately 0.78 and 0.77 attempted replies per fitted episode fail admission in the question-visible arm. The independent arm always writes from its authorized card without a question. [All arms, costs, receipt frequencies and eight final records](results.json)

The source-only replay changes only the writer input. The chooser still hears the original decoded request, respects the same inventory, and pays the same costs. Each selected card uses its actually generated, admitted question-free reply. The resulting distributions exactly match typed transport. This ablation uses cached generations from the same docket and was analyzed after seeing the errors. It does not test how to write a faithful response to an unanticipated question whose wording is needed to select among claims within a card. [Source-only writing replay](question-blind.json)

Training contributes little to routing on this docket. Uniform final-record points tie the initial rule when source-only writing is used. The completion-and-cost objective slightly favors the initial rule at 59.342 versus 59.325. With correlated duplication, the fitted rule improves that same objective over the initial rule from 56.522 to 56.821 and trails exact public planning at 56.985. These differences concern delivery of documentary evidence under a fixed renderer. The test uses same-assistant reviews and no unconstrained final writer, matched solo writing arm, independent deliberation ratings, or new policy optimization.

## Reproduction

From `benchmark-kit/reader-use`, use the project model and Python environment. The archived folder contains the original launch record, token transcript, output manifest and all final report inputs.

```sh
python facilitator_prospective_2593.py verify facilitator-prospective-2593-evidence
python facilitator_prospective_2593.py score facilitator-prospective-2593-evidence
python facilitator_prospective_2593_redaction.py facilitator-prospective-2593-evidence
PYTHONPATH=../../../../src python facilitator_prospective_2593_provenance.py
```
