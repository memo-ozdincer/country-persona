# Judge a concrete source claim before choosing the reply

**The explicit claim improved the reward-calibrated router's held score
from 7.50 to 7.833 on Resolution 2553.** The German desk's prior
prompt chose between two reply cards. The new prompt judges whether
the message's speaker objects to insufficient time on the current
draft. The experiment maps that judgment to the same reply options.
Both runs use two first-token calls per view and the same 64
exploratory reward samples on three calibration contexts. [Protocol](protocol.md)
· [Prior direct router](../reform-2553-transfer/text-reply-transfer/README.md)

| Resolution 2553 policy | Correct /12 | Mean incremental reply points | Mean regret |
| --- | ---: | ---: | ---: |
| Direct router, mean mapped logits | 5 | 7.167 | 1.167 |
| Direct router, reward-calibrated | 7 | 7.500 | 0.833 |
| Keyword rule | 7 | 7.500 | 0.833 |
| Explicit claim, mean mapped logits | 9 | 7.333 | 1.000 |
| Explicit claim, reward-calibrated | 9 | 7.833 | 0.500 |
| Explicit claim, B means supported | 11 | 8.000 | 0.333 |
| True-context ceiling | 12 | 8.333 | 0 |

The reward-calibrated claim policy selects all four genuine matches.
It still sends the timing reply on three negatives, the rejected claim,
the reported claim, and the future negotiation. It removes the prior
router's errors for implementation speed and praise of the timetable.
After averaging, the lowest supported margin is −0.375 and the
highest unsupported margin is −1.5625. Those margins are separated
on this panel. The reward fit from three canonical states did not
place its cutoff inside that gap. The single B-supported mapping's
11/12 is reported as a label-sensitivity result. It was not selected
as a replacement policy. [Matched messages and detailed decisions](results.json)

## Transfer the threshold to Afghanistan

The fixed question asks whether the speaker made their support for
the envoy appointment conditional on agreement from the de facto
authorities. Across eight authored controls, the averaged judgment
at zero recognizes all four support conditions and rejects all four
statement variants without such a condition. The Resolution 2553
reward calibration admits all eight, including all four negatives.
The good same-docket result therefore gives no basis for moving
that numerical cutoff to a new claim. There is no comparable
terminal reply reward assigned to these Afghanistan controls.
[Afghanistan controls](afghanistan-controls.json) · [Documentary source cards](../afghanistan-2721-source-contrast/case.json)

The claim text and its mapping to a reply are supplied by the
experiment. The model verifies the claim from the message. The
reward calculation is conditional on the authored semantic labels
and reuses scored historical reply cards. The held rewrites are
synthetic stress cases, and no new deliberation records were scored.
These are two exposed families and a small assistant-authored panel.
The 46 first-token calls consumed 7,486 input and 92 saved output
tokens on Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition.
All calls and token traces replay and backbone weights stayed frozen.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B collect_claims.py plan | cmp plan.json -
"$python" -B collect_claims.py verify | cmp verified.json -
"$python" -B score_claims.py | cmp results.json -
```
