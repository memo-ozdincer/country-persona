# Assign the opener the downstream value of its report

Hold the proof-aware follower fixed and fit the first desk on the
conditional team return of each feasible action. The accounting feature
set separates four public quantities: standalone decision value,
expected decision value from a possible reply, the opening fee and the
expected reply fee. Conditional eligibility comes from the announced
inventory distribution. The opener has no access to the follower's
actual inventory. One 36-scenario fit uses only the original 0.06 fee.

| Fee per report | Jointly fitted opener | Refit on original features | Ignore follow-up fee | Accounting fit and exact optimum |
| --- | ---: | ---: | ---: | ---: |
| 0.015 | 0.379316 | 0.380247 | 0.380247 | 0.380247 |
| 0.06 | 0.341196 | 0.342081 | 0.342081 | 0.342081 |
| 0.15 | 0.264957 | 0.265749 | 0.265766 | 0.265766 |
| 0.25 | 0.180261 | 0.180951 | 0.184455 | 0.185602 |

Each row replays the same 48 held availability and delivery conditions.
At the training fee the refit closes the small gap even with the old
features. At 0.25 the old-feature refit falls below the optimum in
19 conditions and the rule that ignores reply fees falls below in
eight. The accounting fit reaches the exact result in all 192
conditions. It recovers the four accounting coefficients
`[1, 1, -1, -1]` up to floating-point error. The feature
decomposition supplies the structure of the optimal value function.
The fit recovers the coefficients from simulated team returns.

The matched fixed follower uses the true public fee and the same
certificate status at each price. The comparisons localize the result
to the opener. The outcomes also depend on supplied conditional
availability, transport rates and a known follower rule. This is
action-reward transfer across modeled regimes of two exposed
workshops. [Protocol](opener-credit-protocol.md) · [Weights and
deterministic replay](opener-credit.json)

From this directory in the project Python environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python opener_credit.py | cmp opener-credit.json -
```
