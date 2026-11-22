# Iraq mandate renewal source-record comparison

The source case is the 30 May 2023 Council adoption of S/2023/378 as resolution 2682 (2023). The [pinned cross-benchmark join](../references.json) links UNBench author-test event 2484 to UNSC-Bench adopted row 256 and matches all 15 votes. The accession was rebuilt against the local releases before the experiment. The earlier fictional Iraq workshop exposed the docket. This is its first paired source-record run in the project, and the base model's pretraining exposure is unknown.

The [official meeting record](https://digitallibrary.un.org/record/4012265) records a unanimous vote and adjournment without national explanations of vote. The [adopted text](https://digitallibrary.un.org/record/4012125) separates the 31 May 2024 mandate expiry, the 31 March 2024 independent review deadline and a recurring four-month report. The model receives compact source summaries licensed by the record. The CONSULT summary includes Iraq's letter from the resolution's preamble and the consultation list from paragraph 3. Both desk roles are fictional analysts of different parts of the same document. There is no stage for national bargaining and no minority objection to infer from this meeting.

The official PDFs retrieved through the UN documents API had SHA-256 digests `f03d5e9ff86d91d1591a5409cbc50ed128b8ce11c898ca65c8e0852e7042953a` for S/PV.9331 and `9767921f849af3a1de19e8e1c5387261fb877478586d2b120d473c9bccd26fd4` for S/RES/2682(2023). The [frozen case](case.json) assigns ten seven-point criteria and separate material guard checks.

## Matched generation and review

Each condition has four working turns, one synthesis and a ceiling of 688 output tokens. The two team conditions share their openings and role-specific sources. Interactive revision additionally sees the other desk's opening. The pooled analyst sees both openings at revision and the full evidence packet throughout. All final writers get the full packet and two provisional revisions under the same synthesis prompt. That makes this a test of how working notes influence a fully informed final writer. Actual prompt sizes differ by design and are reported below.

| Condition | Final record out of 70 | Words | Input tokens | Output tokens | Guard clear |
| --- | ---: | ---: | ---: | ---: | --- |
| Pooled solo | 28 | 134 | 3,076 | 575 | No |
| Independent drafts | 35 | 149 | 2,299 | 633 | No |
| Interactive drafts | 35 | 149 | 2,494 | 637 | No |

All three final records extend the requirement for full, equal and meaningful participation directly to civil society and youth. The adopted text asks that their input be considered and explicitly gives the participation standard for women. All three omit the full independent-review deliverable as specified, including who was to submit it and to whom. The interactive condition names the draft and covers the review's recommendation scope. The independent condition covers the absence of national explanations and the regional-cooperation assessment. The interactive chair stops mid-sentence at the token cap, while the pooled first revision reaches its cap. Raw supported spans receive their semantic points before the citation and completion guards.

The bounded [source-idea inventory](evidence/process-results.json) tracks exact spans for 13 preselected types of proposition. Across opening and revision it matches six distinct ideas for the independent mandate desk and four for the independent review desk, against five and four for the interactive desks. The two solo working slots cover five each for one analyst. Neither team revision shows a tracked idea uniquely attributable to the peer opening after comparison with the corresponding independent revision. The interactive final's draft identifier is new relative to both of its supplied revisions and present in its full source packet. These are conservative phrase-matched counts and leave other ideas uncounted.

The [final-record annotations](annotations.json) are same-assistant review against the sources. The separate automated judge receives an opaque candidate, one frozen criterion, one source block and three semantic labels in two orders. It has no access to the party labels or draft transcript. The calibration includes omissions, incompatible claims and unchanged neighboring criteria, alongside all 30 generated record units. The judge is a diagnostic for factual coverage, and the existing transcript rubric separately defines process, reasoning and causal uptake. [Final records](evidence/final-records.json) · [Transcript rubric](../../discussion/process-judge.md)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" episode.py preflight
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" episode.py replay evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" judge.py review
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" process.py
```

A retrospective partial-credit check gives half a criterion's points to a named surviving clause. It produces 45.5/70 for the pooled analyst and 49/70 for each team. The three guard failures persist. The prespecified complete-criterion scores remain the primary results. [Partial-credit spans](evidence/partial-credit.json)

## Judge calibration on actual records

The frozen Qwen3.5-4B judge agrees in both label orders on the correct classification for 17 of 20 authored checks. It gets all 15 supported checks, one of three contradictions and one of two omissions. On the 30 units across the actual final records, it calls every unit supported in both orders. The source review supports 14 units, finds 13 omissions and identifies three contradictions. This judge would give all three final records full coverage, including the one that stopped mid-sentence. Case-specific controls must include actual incomplete outputs, and order agreement alone cannot serve as a quality gate.

The model record replay checks 13 exact prompt and output-token sequences. Judge replay checks all 100 prompts, choice token IDs, and saved logits. The judge uses the same frozen checkpoint as the writer. The manual evidence review and its controls are same-assistant work. These artifacts establish an observed evaluator failure on this case. They supply no independent human quality estimate or training reward.

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" judge.py report judge-evidence
```

[Calibration labels and score comparison](judge-evidence/results.json)

## Judge candidate text before comparing with the archive

`witness_judge.py` selects verbatim candidate windows with an exact offset for each one. The same frozen Qwen checkpoint receives those windows, a question about what the writer asserted and a case-specific value menu. The source block is withheld. The menu still includes the correct historical value as one possibility. Two answer orders map back to the same semantic values, and disagreement or absent retrieval refers the criterion for review. These changes were made together after reading the original errors. Their individual effects remain unmeasured.

On the 30 generated criteria, the excerpt judge agrees with the source review on 27. It preserves all 14 valid units, catches all three contradictions, labels ten of 13 omissions correctly, overcredits two omissions and defers one. It would grant 35, 42 and 35 provisional points to the solo, independent and interactive records, against the reviewed 28, 35 and 35. Its seven-point apparent preference for independent drafts comes from misreading evaluation as a commitment to make recommendations. On the 20 shared authored checks the new judge gets 15, down from 17 for the original judge. On the expanded panel it gets 17 of 24, defers six and grants false credit to an incorrect review recipient. All 104 prompt encodings and decision tokens replay exactly. [Evidence windows and decisions](witness-evidence/results.json) · [Reward distortion on the same records](witness-evidence/reward-audit.json)

A deterministic prerequisite for three selected fields withholds the two observed false credits and the wrong-recipient foil without losing a valid point on the generated panel. The same gate loses a correct authored consultation statement. Among ten additional scope and language controls it also rejects a valid consultation paraphrase and accepts a recommendation found only inside a counterfactual. These results support its use as a review referral on this narrow case. A text match cannot establish binding, event status or entailment. [Prerequisite controls](witness-evidence/gate-results.json)

The independently replayable retrieval audit separates whether the judge saw a known witness from how it classified that witness. Lexical ranking of two candidate sentences retains all 17 reviewed supporting or contradicting witnesses in Iraq and 58 of 59 in Western Sahara. The missing Western Sahara sentence attributes disregard of Algeria's views to the Council rather than the penholder. Three candidate sentences recover it, with roughly 44% of full text characters in Iraq and 63% in Western Sahara. Citation-only retrieval loses one witness in Iraq and 20 in Western Sahara. These figures measure previously annotated spans in nine existing records and leave the generalization of the semantic judge open. [Retrieval audit](evidence/retrieval-audit.json)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" witness_judge.py report witness-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" reward_audit.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" witness_gate.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" retrieval_audit.py
```

## Replay frozen routes through the final writer

The routing experiment supplies one of 14 reachable nonempty receipt sets to frozen Qwen3.5-4B. The prompt asks for a retrospective supplement of at most 106 words, with a separate line and exact source ID for each received card. It supplies no text from undelivered cards. The compiler prefixes the same authored public paragraph in every arm. That paragraph contributes 28 points for vote, term and recurring reporting. The learned route, public payoff alignment and best authored-score fixed and adaptive scripts are frozen before generation. A full-target solo writer receives all three requested cards immediately. That arm shares the generation ceiling and has an information advantage.

The same-assistant exact-span review found every criterion licensed by each receipt set in the corresponding unedited text. All 14 outputs ended within the token and word caps. The model largely preserved the supplied summaries verbatim. Three outputs miss the line-format contract. The CONSULT singleton and CONSULT-plus-SCOPE packet repeat a source ID across lines, and the SCOPE singleton puts its citation on a separate line. Keep the wording review and output contract separate.

| Route | Final record out of 70 | Release probability before formatting | Expected points on releasable records |
| --- | ---: | ---: | ---: |
| Protected card only | 38.50 | 50.00% | 19.25 |
| Direct frozen policy | 51.57 | 89.01% | 46.62 |
| Best fixed script | 52.43 | 87.78% | 46.86 |
| Aligned frozen policy | 52.61 | 87.70% | 47.01 |
| Best adaptive script | 52.82 | 88.43% | 47.57 |
| Solo with the full target packet | 59.50 | 100.00% | 59.50 |

The aligned policy leads the fixed schedule by 0.162 net points after message costs and the adaptive script leads the aligned policy by 0.214. The main comparison uses one writer per packet and the original raw output. The reply swap lowers the aligned score from 52.61 to 52.42. A posthoc planner that sees the generated score bank recovers the same raw-score plans and can improve release-qualified scores slightly. A separate composition of singleton generations preserves the factual coverage but spreads singleton citation defects to larger packets. It has a different writer-call budget. [Records and route distributions](receipt-evidence/results.json) · [Singleton composition and retrospective planners](receipt-evidence/controls.json)

A posthoc layout normalizer combines adjacent clauses with the same trailing citation and moves detached trailing citations onto their source line. It preserves all words outside citation IDs in their original order. All 14 reviewed records then satisfy the format and length checks. The parser rejects missing or unexpected IDs, leading citations, interleaved duplicate IDs, and unassigned trailing text in five controls. The review of source fidelity is separate. [Citation-layout control](receipt-evidence/format-control.json)

This is a bridge from learned transport to actual model-written records on an exposed source case. It shows that routing gains can survive a source-local writer where the evidence fits its budget. Independent semantic review, fresh event families and free-form agent discussions remain separate evaluation requirements.

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_writer.py replay receipt-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_score.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_controls.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_format.py
```
