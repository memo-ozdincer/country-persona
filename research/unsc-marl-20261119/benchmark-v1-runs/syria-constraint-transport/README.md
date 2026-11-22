# Pass the peer's constraint separately from its recommendation

A source-reviewed projection passes only the opening speaker's stated
fictional constraint into the second desk's existing peer-note field.
It omits the recommendation and historical restatement. The same
projection then enters the final writer with the fresh, unedited
second note. The role, private evidence, source blocks and generation
limits stay fixed. Qwen3.5-4B runs on NVIDIA RTX PRO 6000 Blackwell
Server Edition without optimizer updates. The comparison uses both
Syria mandate variants and both speaker orders.

| Treatment | Second desk retains own requirement | False package endorsements by any desk | Notes certify the decision | Correct final decisions | Released final points /280 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Independent drafts | 4/4 | 0 | 2/4 | 0/4 | 0 |
| Raw peer note | 3/4 | 1 | 2/4 | 0/4 | 0 |
| Constraint-only peer note | 4/4 | 0 | 2/4 | 1/4 | 70 |

In Brazil-first overlap, the UK reply stops endorsing A. It retains the
checkpoint requirement, but incorrectly says Brazil voted against the
second historical draft. Brazil abstained. The final drops that historical
error and remains unresolved. In UK-first overlap, Brazil restores its
nine-month requirement and repeats the UK checkpoint condition. It still
recommends A, a package it can accept locally. The joint writer copies A
instead of choosing B. Both overlap notes are enough to recover B if their
stated constraints are treated as complete. Neither strictly certifies
mutual compatibility. The treatment does help uncover a correct decision
in one impasse final. The total input for the second desk and writer falls
89–110 tokens relative to raw peer visibility.
[Protocol](protocol.md) · [Raw notes and finals](evidence/episodes.json) · [Source and review spans](reply-marks.json) · [Final grades](final-marks.json) · [Per-condition scores](results.json)

The opening projection was authored by the same assistant that scored
the outputs, using a quote in each archived opening note. The replay
tests the evidence that enters the channel, the receiving agent's
behavior and final writing separately. It leaves automatic extraction,
learned policy gains and transfer beyond this exposed docket open.


## Cross the two writer inputs

The UK-first impasse supplied the single exact gain. Hold the writer and
caps fixed and cross its two opening and reply versions. The UK-first
case was selected after inspecting the successful record.

| Opening shown to writer | Brazil reply shown to writer | Decision | Words | Released score /70 |
| --- | --- | --- | ---: | ---: |
| Raw | Raw peer reply | UNRESOLVED | 168 | 0 |
| Raw | Reply to projected opening | UNRESOLVED | 46 | 28 |
| Projected | Raw peer reply | UNRESOLVED | 44 | 0 |
| Projected | Reply to projected opening | IMPASSE | 46 | 42 |

With the fresh Brazil reply held fixed, the two final records have
identical prose below their first line. Restoring the original opening
changes only the decision line from `IMPASSE` to `UNRESOLVED`.
This case separates the chair's disposition from its explanation.
The chair was sensitive to both the direct presentation of the opening
and the second delegate's response to it.
[Crossed prompts and records](crossover-evidence/crossed.json) · [Quote-backed marks](crossover-marks.json) · [Scored crossover](crossover-results.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
python replay.py verify evidence | cmp verification.json
python score.py reply | cmp reply-packets.json
python score.py final | cmp final-packets.json
python score.py score | cmp results.json
python crossover.py verify crossover-evidence | cmp crossover-verification.json
python score_crossover.py deck | cmp crossover-packets.json
python score_crossover.py score | cmp crossover-results.json
```
