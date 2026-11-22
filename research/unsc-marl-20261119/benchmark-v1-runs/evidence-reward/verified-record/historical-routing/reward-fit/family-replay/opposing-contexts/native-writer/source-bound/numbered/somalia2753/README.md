# Transfer the coordinated router to Somalia's 2024 mission transition

This case entered the routing evaluation for the first time in this
run. Its public record can have appeared in language-model pretraining.
The archived UNBench meeting and draft join on S/PV.9764 and
S/2024/790. Searching the pinned 258-row adopted UNSC-Bench file finds
no corresponding row. The ballot and mandate are verified against the
official record. Menus are concise, attributed paraphrases tied to
that record. [Dataset lineage](lineage.json) ·
[Official meeting record](https://digitallibrary.un.org/record/4065111) ·
[Adopted resolution](https://digitallibrary.un.org/record/4065090)

The source packet and rubric were locked before the three isolated
Qwen3.5-4B calls. The China–Somalia procurement criterion and the
China–U.S. distinction gave two equally weighted dependency pairs.
The five-grade rule breaks that tie in slot order and reviews
China–Somalia. Seven grades supply all three pairs. Both settings
withhold the full three-card grade from policy selection.
[Protocol](protocol.md) · [Frozen case](case.json) · [Plan](plan.json)

## Final record and format control

| Processing | Full record | Words | Interpretation |
| --- | ---: | ---: | --- |
| Strict string-list protocol | 49/70 | 106 | Rejects China's integer list |
| Post hoc numeric-ID replay | 70/70 | 150 | Admits the same valid China IDs in their original order |
| Ordered authored menu | 70/70 | 150 | Identical released grades across all eight masks |

The China call returned two valid role-local IDs as integers. The
replay converts literal integers to decimal strings and reuses the
original role-membership and duplicate checks. Other malformed values
remain inadmissible. The final record retains the shared procurement
point, Somalia's emphasis on employing Somali women, the U.S.
reporting reservation despite its yes vote, and the conditional
intention to end the mandate in October 2026.
[Raw calls](evidence/calls.jsonl) · [Parser control](numeric-format.md) ·
[Strict records and marks](grades.json) · [Numeric replay records and marks](numeric-grades.json)

## Adaptive and fixed routing with the same information

Each row below summarizes 18 modeled conditions. The three inventory
blends are each evaluated with a correct or dominant-only advertised
law. The designated pair's grade varies by zero or one criterion in
either direction. Fixed and adaptive routing get the same calibration,
prior and message costs.

| Processing and review budget | Interval team wins | Losses | Mean net gain over equally informed fixed |
| --- | ---: | ---: | ---: |
| Strict, five grades | 12 | 1 | +0.0263 |
| Strict, seven grades | 12 | 1 | +0.0263 |
| Numeric replay, five grades | 13 | 1 | +0.1175 |
| Numeric replay, seven grades | 15 | 1 | +0.1176 |

Seven grades with numeric replay also beat fixed routing given the
true bank and inventory law in 15 of 18, losing three. The mean margin
is +0.0636. Documentary scores stay at or above optimized silence in
the 18 numeric-replay conditions. Two additional reviews improve the
win count and show little change in average gain over equally informed
fixed routing. Review effort and inference are separate from message
cost. The dispatcher reconciles selected zero-error analytical results
and preserves witness records. The routing gain survives the ordered
menu control, where native ranking contributes no extra scored quality.
[Strict routing](results.json) · [Numeric replay and dispatcher](numeric-results.json)

These results cover one newly evaluated docket with authored menus,
same-assistant source and rubric checks, and simulated delivery.
They measure an encoder and router in a source-bound record pipeline.
The three native calls ran on an NVIDIA RTX PRO 6000 Blackwell Server
Edition with the base checkpoint frozen. Independent review and
generalization across new docket families remain open. The first launch
stopped before generation because a JSON round trip converted integer
keys in the plan to strings. The corrected launch kept prompts and
semantic settings identical. [Native verification](verification.json) ·
[Rejected launch](preparation-rejected/launch.json)

Run in the parent Python environment.

```bash
set -o pipefail
sha256sum -c assessment.sha256
python3 somalia_transfer.py plan | cmp - plan.json
python3 preflight.py | cmp - preflight.json
python3 somalia_transfer.py verify | cmp - verification.json
python3 evaluate_somalia.py grades | cmp - grades.json
python3 evaluate_somalia.py replay | cmp - results.json
python3 numeric_control.py grades | cmp - numeric-grades.json
python3 numeric_control.py replay | cmp - numeric-results.json
uv run --no-project --with pyarrow==25.0.1 -- python lineage.py | cmp - lineage.json
```

[Live passage transport](live/README.md) checks two Somalia branches
with fresh role generation, component swaps and query erasure. It
separates getting the right source card from preserving the key
position inside that card.
