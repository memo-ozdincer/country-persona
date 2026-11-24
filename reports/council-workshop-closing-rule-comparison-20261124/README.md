# How the closing rule affects Council benchmark scores

The registered protocol scores an impasse after a delegate declares
it. This offline audit reruns the same decisions with the existing
moderator rule, which certifies an impasse immediately when every
package has a checked public exclusion. It verifies each saved
model request up to the stopping point and uses zero new calls.

| Registered meetings | Delegate declaration | Moderator closes on complete evidence |
| --- | ---: | ---: |
| Feasible agreements | 7 of 7 | 7 of 7 |
| Certified impasses | 3 of 7 | 5 of 7 |
| Total successful outcomes | 10 of 14 | 12 of 14 |

Two capped meetings already had enough evidence. In the
Norway-opening mixed Gulf run, the last exclusion arrived on speech
ten, so changing the closing rule certifies the impasse at the same
call count. In the UAE-opening all-Sol Iraq run, it arrived on call
53, with two subsequent floor calls exhausting the budget. The
other two unresolved runs were still missing an exclusion under
either procedure. The moderator closed three already successful
impasses earlier. Across all 14 meetings the replay saved 12 calls.
The interrupted UAE-opening mixed run has no terminal score.

In the Norway-opening Gulf comparison, the seat swap's reward delta
changes from −1 to 0. The other five completed paired deltas stay
fixed. Each comparison uses one trajectory per assignment.
This audit measures a stopping-rule change on existing decisions.
The registered model results continue to require delegate declaration.

```sh
set -o pipefail
out=reports/council-workshop-closing-rule-comparison-20261124
python3 -B "$out/compare.py" | cmp "$out/results.json" -
```

[Frozen run list](paths.json) · [Replay results and paired deltas](results.json) ·
[Registered scorecard](../../research/council_workshop/SCORECARD.md)
