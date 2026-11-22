# Replay follow-up requests through the final-record rubric

The 44 archived Iraq and Syria presentations now produce a final
record on every enumerated delivery branch. The chair copies official
facts into the historical section, uses the public sign ledger for
the decision, and labels inferred and directly disclosed mandates.
It describes ambiguous mandates as such. The second reply is the
authenticated role declaration from the earlier archive. Some of the
actual question contexts differ from those in this replay.
[Protocol](protocol.md) · [Renderer](render.py) · [Branch provenance](replay.json)

All 16 distinct texts were reviewed against the frozen v1.1 rubric
using exact source quotes. Each clears the guard. Uncertified
decisions receive zero released points as required by the benchmark.
An agreement with only one identified mandate earns 56/70 in this
review. Delivering the missing declaration raises that to 70/70.
Exact decision counts stay at 16.80 expected in every arm.

| Follow-up delivery | No follow-up, released points | Prior value heads, released points | Prior value heads, net change from silence | Rubric-weighted heads, extra questions |
| ---: | ---: | ---: | ---: | ---: |
| 0.20 | 1,131.20 | 1,131.20 | 0.0000 | 0 |
| 0.55 | 1,131.20 | 1,155.84 | −0.0960 | 0 |
| 0.70 | 1,131.20 | 1,162.56 | 0.0000 | 0 |
| 0.80 | 1,131.20 | 1,167.04 | +0.0640 | 3.20 |

These are totals across 44 presentations, with delivery branches
weighted by probability. Net divides released points by 70 and
subtracts modeled costs. At 0.80, the request adds 35.84 expected
released points and raises full-rubric passes from 13.60 to 16.16.
At 0.55, it recovers 24.64 released points before costs. The frozen
joint team asks even at 0.20, where it gains 8.96 points and loses
0.3200 net. The earlier proxy rewarded a successful follow-up at
0.50. The reviewed outputs gain 14/70, or 0.20. With 0.14 combined
question and send cost, that raises break-even from 0.28 to 0.70.
[Masked texts](deck.json) · [Marks](marks.json) · [Scored replay](scores.json)

## Fit with the published attribution weight

Using the existing synthetic paths, refit the two value heads with
the 14-point weight from the published rubric. Held texts and verdicts
are used only for evaluation. The fitted policy stays silent at
0.55 and 0.69, breaks ties in favour of silence at 0.70, and keeps
the same coverage gains at 0.71 and 0.80 as the previous heads. At
0.55, it recovers 0.0960 net relative to the previous value heads
while forgoing 24.64 released points. A different scoring increment
would set a different threshold. For example, recovering two
14-point items would lower break-even to 0.35 under the same costs.

This is a dependent, same-assistant replay of two previously exposed
families using typed proof and deterministic prose. The current fit
knows the configured delivery probability and cost. It adds zero
Qwen calls or updates and allows no claim of improved live dialogue
or generalization to other document types. The first refit attempt
resolved the wrong calibration module. The corrected run scopes the
imports to the matching experiment; the original frozen benchmark
and recorded grades replay unchanged.
[Refit protocol](reweight-protocol.md) · [Weights and six-rate comparison](reweighted.json)

## Verify

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 replay.py replay | cmp - replay.json
python3 replay.py deck | cmp - deck.json
python3 replay.py score | cmp - scores.json
python3 reweight.py | cmp - reweighted.json
```
