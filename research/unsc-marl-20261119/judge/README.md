# Benchmark-backed evaluation of single and multi-agent UN deliberation

UNBench contributes co-penholder, vote, adoption and statement tasks. UNSC-Bench contributes P5 vote prediction with adopted and vetoed drafts. The first two calibrated rows are the UNBench Task 2 author-test row for S/2022/925 and UNSC-Bench vetoed row 11 for S/2023/970. The bridge verifies release hashes, identifiers, date and selected vote labels against the previously checked roll calls. Author-test membership does not make a previously used project case held out. [UNBench paper](https://ojs.aaai.org/index.php/AAAI/article/view/37040) · [UNSC-Bench paper](https://aclanthology.org/2026.mme-main.10/) · [Exact benchmark rows](benchmark-development.json)

For the larger pack, retain native results separately for each benchmark and each task. UNBench's author-test vote set is 6,210 yes, 209 abstain and one no, so always-yes already gives 96.73% accuracy. Include minority-class recall and joint correctness on historically disagreeing delegation pairs. The pinned audit found 236 common draft symbols across releases and flagged 42 of the 469 UNSC-Bench records for review. Split by related drafts and meetings across both releases, including translations, and hold out whole negotiation families. Keep the pre-vote version and actual elapsed-time cutoff explicit. Primary roll calls determine objective labels. A language judge grades grounded explanations and simulated decisions. [UNBench audit](../../../reports/eval-pilot-20260926/unbench-audit.json) · [UNSC-Bench audit](../../../reports/eval-pilot-20260926/unsc-bench-audit.json)

## Comparison protocol

Run on the same case and evidence cutoff. Compare a direct single analyst, role drafts revised independently and synthesized, and revision with actual peers followed by the same fixed synthesizer. Use the same openings for the revision arms, the same per-arm generation ceiling, the same final contract, and a shuffled-peer control when feasible. Record actual input and output tokens and any information access differences. Use separately labeled native benchmark and source-augmented results. In prediction, the model and the judge scoring its rationale do not receive the historical vote key. The mechanical score has separate access to that key.

Give the final-record judge randomized opaque IDs, no transcript and no model or condition label. Score the five case-specific final criteria out of 70 points, with anchored key points and arguments as separate diagnostic scores when supplied. Track critical fabrication of a vote, official commitment, collective endorsement or source authority as a guard. Preserve uncertainty in score bounds. The transcript judge receives the actual peer turn, recipient opening and revision, and matched solo revision. It grades whether an identifiable contribution carried through; no credit for polish or coincidence. Count valid peer opportunities and incorrect adoptions separately.

The [exact system prompt](instructions.md) instructs the judge to cite verbatim spans from supplied evidence and the candidate response, identify what the span establishes, and distinguish an omitted answer from a contradiction. The [validator](score.py) checks quotation containment and criterion coverage and performs all arithmetic. Quote containment does not establish entailment. For held-out tests, use randomized order, independent judge repetitions or human double coding, and adjudicate disagreements against primary source spans. Archive raw judge output, exact input, rubric hash, model identity, evidence and score. Scores on curated anchors demonstrate calibration coverage, with agreement against real independent verdicts still to be measured.

## Exercised cases

- Four authored final anchors exercise a correct record and a plausible false-consensus variant on each benchmark. Scores are 70 and 14 on the UNBench case, and 70 and 0 on the UNSC-Bench case. Both fabricated records trigger the guard. A separate transcript anchor earns peer credit. The validator rejects an invented quote and a peer-specific grade without matched solo history. [Calibration requests and verdicts](calibration.json)
- Two previously generated UNSC-Bench-linked full memos pass quotation validation under a new retrospective rubric. The base scores 70/70 but overclaims a shared priority and fails the fabrication guard. The adapter scores 56/70 because it leaves the veto mechanism implicit, while clearing the guard. Both fail the strict contract. This example shows the value of keeping the guard visible beside the points. [Archived UNSC-Bench memo scores](archived-memo-scores.json)
- For the archived climate debate, provisional retrospective grades give solo and peer revision 14/70 each. The direct analyst spans 42–56/70. All three fail the guard for inventing a documented UK position on binding quotas. This is a real output exercise with known arm identities and unequal actual costs. It cannot rank methods on new meetings. [Archived comparison](archived-deliberation-review.json)

There was no separately run judge model, independent review or fresh deliberation output in this checkpoint. Keep the archived exercises as development data. The next generalization check is an opaque-ID evaluation on fresh source-audited negotiation families under the comparison protocol.

## Local replay

From this directory, run:

```bash
python calibration.py /tmp/unsccalibration.json
python compare.py archived-memo-review.json
python compare.py archived-deliberation-review.json
```

To make a judge packet, save one request from `calibration.json` and pass it to `python score.py packet.json`. The output contains separate system and user messages. Pass the returned judge JSON to `python score.py packet.json --verdict verdict.json`. Run `benchmark_rows.py` with `PYTHONPATH=src` from the project root in the existing PyArrow environment to rejoin the pinned archives.

## Historical authority and current workshop status

The [final-record anchors](evidence/authority/final-anchors.json) take five signed Myanmar and Mali traces and verify their public certificate independently. Every accurate record scores 70 under its authored reference, including the cases that remain unresolved. In each foil, only the authority sentence changes. It claims that a workshop outcome gained official force, which changes the authority item and fabrication guard while the other four items remain identical. The resulting score is 56 and the strict contract fails. Reproduce the inputs, exact spans, and scorecards with `python workshop_final_anchors.py`.

## Required facts and local contradiction checks

The Western Sahara pilot used five compound final criteria. A 16-part diagnostic preserves the same group weights and guard. It can measure coverage without treating one omitted detail as a complete loss of credit for its group. The six records are rescored with exact output spans from the archived responses, source IDs and the original critical-error judgments. The review is posthoc, unblinded and by the same assistant. It does not replace the originally reported endpoint. [Rubric](minurso-atomic-rubric.json) · [Part-level scores](../benchmark-kit/evidence/source-record-minurso/atomic-score.json)

The initial frozen Qwen3.5-4B judge gives the correct label in both presentations for 30 of 35 criterion and record pairs. Always selecting the support position gets the same count. Four of five contradictory edits are unanimously marked supported and none is always detected. Two test design defects were identified. Supported stayed at B and the omission foil repeated the missing fact later. The score corrects the omitted case's authored label to supported and retains both values. These results do not support using this judge as a final-record reward. [Raw decisions and adjudicated score](../benchmark-kit/evidence/source-record-minurso-atomic-judge/score.json)

The corrected panel rotates each answer meaning through all three letters. It checks 18 distinct record and criterion pairs, including one genuine omission and five incompatible claims. Frozen Qwen3.5-4B unanimously accepts 12/12 supported items. It also unanimously accepts the omission and four contradictions. Only the adopted-authority foil changes verdict with answer order, and it is caught in two of three orders. The mean probability of a valid answer letter is 99.96%. This is stable false acceptance with a well-formed output. The next experimental distinction is between extracting the position the candidate actually states and rating it against the authorized record. Passing the gold fact and the source in the same prompt could let the judge answer about either instead of the candidate. These results do not identify the internal cause. [Control script](minurso_atomic_controls.py) · [Raw classifications and exact replay](../benchmark-kit/evidence/source-record-minurso-atomic-controls/score.json)

Replay with the local analysis Python environment from this directory.

```bash
python minurso_atomic_review.py manual ../benchmark-kit/evidence/source-record-minurso/atomic-annotations.json
python minurso_atomic_review.py model ../benchmark-kit/evidence/source-record-minurso-atomic-judge
python minurso_atomic_controls.py report ../benchmark-kit/evidence/source-record-minurso-atomic-controls
```

## Compare extracted candidate values to the source key

The candidate-only arm uses the same 18 Western Sahara record and field pairs and three answer layouts. Each prompt contains the whole candidate record, a neutral field and a menu of three possible values. It supplies neither the evidence blocks nor the correct value. A deterministic comparison with the same frozen facts follows model inference. The method converts label disagreements and ties into unresolved results. [Extractor](minurso_candidate_fields.py) · [Exact result](../benchmark-kit/evidence/source-record-minurso-candidate-fields/score.json)

| True status | Pairs | Correct in all orders | Wrong in all orders | Unresolved |
| --- | ---: | ---: | ---: | ---: |
| Supported | 12 | 11 | 0 | 1 |
| Contradicted | 5 | 2 | 0 | 3 |
| Omitted | 1 | 0 | 0 | 1 |

The source-and-answer judge accepted five flawed edits consistently, including the omission. Candidate-only scoring withholds points for all six flaws and gives a positive margin to the faithful member for five of the six pairs. Both methods preserve the adjacent unchanged record facts on all six pairs. For national capacity, the candidate-only reward ties because it also withholds credit from the faithful reference. The prompts use closed task-specific menus and only the extracted value is scored. These are adaptive checks of an exposed docket. An unresolved field is neither a verified omission nor a verified contradiction. [Matched reward audit](../benchmark-kit/evidence/source-record-minurso-candidate-fields/reward-pairs.json)

The same extractor and deterministic scoring rule transfer to three field types from the archived Mali and DPRK dockets. The panel takes the authored Mali control and an actual model-generated DPRK record. For each field it adds one minimal contradictory edit and one omission. All three contradictions are correctly extracted in all orders. Two of three supported items and two of three omissions are also consistently correct. The Mali omission ties in one order. For the faithful DPRK statement, the model confuses Yamazaki's office as Council President with the national capacity in which the record says he spoke. This gives two incorrect readings in three orders. Requiring agreement withholds that case, while majority voting would classify it as a contradiction. Scope and capacity remain a substantive limitation. This is transfer of an extraction procedure across previously exercised project dockets, with case-specific menus and no optimization. [Transfer panel](institutional_candidate_fields.py) · [Archived field judgments](../benchmark-kit/evidence/institutional-candidate-fields/score.json)

Reproduce the scorer outputs from this directory.

```bash
python minurso_candidate_fields.py report ../benchmark-kit/evidence/source-record-minurso-candidate-fields
python minurso_reward_pairs.py
python institutional_candidate_fields.py report ../benchmark-kit/evidence/institutional-candidate-fields
```
