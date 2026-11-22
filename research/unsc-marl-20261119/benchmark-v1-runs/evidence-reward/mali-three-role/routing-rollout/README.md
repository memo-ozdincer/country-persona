# Re-evaluate questions under asymmetric delivery

The learned chair's predicted action values were miscalibrated when the
technical desk's delivery fell to 0.35. Keep its frozen continuation
policy, but score a proposed question by the downstream returns under
either possible sign and under no delivery. Include the option to stop.
Recompute these choices at each step. The workshop, reward, decision
rule, private-world prior, and model-free comparisons are unchanged.

| Questions available at delivery rates 0.90 / 0.80 / 0.35 | Frozen chair | Fixed order | Rollout with learned continuation | Exact planner |
| --- | ---: | ---: | ---: | ---: |
| 2 | −0.0251 | −0.0060 | 0.0650 | 0.0650 |
| 3 | 0.1284 | 0.1638 | 0.2209 | 0.2209 |

Figures are expected normalized documentary proxy after communication
costs. The rollout opens with the second desk instead of the technical desk.
At three questions, its mechanical accuracy rises from 32.7% to 49.0%.
Across 19 valid delivery profiles and three budgets, it improves on the
frozen policy in 30/57 conditions and ties it in the rest. It matches
exact planning in 51/57. Its worst expected-net shortfall from exact
planning is 0.007074, versus 0.096919 for the frozen chair.

The rollout with a one-step greedy continuation also repairs the original
asymmetric failure and matches the learned-continuation rollout at equal
rates and three turns. Across all conditions, the learned continuation wins
six, loses two and ties 49 against the greedy continuation. It beats the
fixed-order continuation in 38 and ties 19. These comparisons suggest the
main improvement is the explicit delivery branching. Exact planning remains
feasible here. The three rollout variants together cache at most 158
continuation state, budget and policy combinations per condition.

A separate mismatch check overestimates the weakest desk's delivery as
0.90 on the two asymmetric profiles. The learned-continuation rollout
matches the resulting planner in all four tested combinations. It receives
the same inaccurate rate as that planner. This check leaves open how to
estimate changing rates from observed responses.

The evaluation enumerates outcomes on one exposed fictional workshop
derived from the Mali docket. Rate permutations and budget variants are
controlled conditions. Results use no new model calls or optimizer
updates. The [live traces](../live/README.md) have a distinct evidentiary
scope. [Protocol](protocol.md) · [All results and pins](results.json)

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 rollout.py | cmp - results.json
```
