# Review procedure

## Calibrate on authored examples

For an adapter judge, run `python3 run_suite.py calibrate judge.json judge-calibration`
before scoring model outputs. Save `calibration.json`, the raw JSONL and
both verdict maps. Inspect attribution, scope and guard mismatches against
the cited text. Incomplete coverage fails the calibration command, while
valid verdicts that disagree with authored labels remain visible as
mismatches. Keep the rationale for using or revising the judge with the
calibration receipt. The anchor scores describe agreement on exposed
examples.

For manual calibration, export the two sets.

```bash
python3 calibrate.py > final-anchors-packets.json
python3 calibrate.py --mode process > process-anchors-packets.json
```

Use [the final instructions](final-judge.md) for the first export and
[the process instructions](process-judge.md) for the second. For each opaque
packet ID, return the full verdict specified by its instructions. Save a
JSON object mapping packet IDs to verdicts separately for each mode.

```bash
python3 calibrate.py --verdicts final-anchor-verdicts.json
python3 calibrate.py --mode process --verdicts process-anchor-verdicts.json
```

The 21 final anchors include 11 authored full-credit targets, one per
episode. Ten additional examples cover omissions, supported positions,
vote errors and unsupported authority. The four process anchors test a correction that
survives into the record, a correction lost at synthesis, parallel drafts
and repeated wording. Inspect every mismatch and retain counts and raw
verdicts. The process prompts check selected ratings while still requiring
a complete, valid verdict. These authored labels are exposed calibration
examples.

## Blind both readings

Export review packets from the completed actor matrix. Give an independent
reader the packets and the two judge instructions. Keep actor identities,
condition names, the first set of grades and anchor keys outside this
review. Transcript visibility and speaker names are necessary for process
evaluation. The reader returns one JSON object with maps named `final`
and `process` from packet ID to full verdict. Preserve both original
readings before comparison. Use the version and configuration in the
associated actor and judge launch receipts to identify the run.

Resolve differences from the supplied sources and exact transcript spans.
Save the reasons and the resolved verdicts alongside the originals. Inspect
idea ledger disagreements even if the total counts agree, especially merges,
claim attribution and whether a source-supported objection survives the
final. The scorer validates quote membership and rating structure. A quote
match alone cannot establish that the source entails the claim. Report exact
criterion and guard agreement, the guard confusion table, release decisions
and exact released-score agreement. In `agreement.json`, check
`outcome_sensitivity` for changes in the direction of peer-minus-independent
or peer-minus-solo, including ties, by track and by family and speaker order.
Preserve the two original comparisons and any adjudicated comparison.
The `apply` command computes scores from supplied marks. Record separately
whether the marks are one reading, a consensus, or a third-reader
adjudication. Retain quote spans and reasons on both sides of any disputed
criterion that changes the result. Exact agreement on a small number of
shared packets is descriptive. Record how many unique packets were reviewed.
Keep all failures in the matrix. Software fixtures check the
contract and are separate from judge calibration and actual model quality.

## Recover invalid judgments

If the judge runner reports incomplete coverage, retain
`coverage.json`, `invalid-judgments.jsonl` and the raw `judges.jsonl`.
Export the valid readings.

```bash
python3 review.py extract-marks judge-run/valid-marks.jsonl > partial-marks.json
```
Use the packet IDs in `invalid-judgments.jsonl` to locate the missing
packets in the blinded export. Multiple conditions can share a packet.
Review each missing packet once per mode, save the replacements, and
merge them into the `final` and `process` maps in `partial-marks.json`
by packet ID. Save the merged file separately.

```bash
python3 review.py apply actor-run/episodes.jsonl recovered-marks.json > recovered-report.json
```

The command checks complete coverage against the original actor episodes
before scoring. Report the number of distinct packets repaired and who
supplied the replacements alongside the result.
