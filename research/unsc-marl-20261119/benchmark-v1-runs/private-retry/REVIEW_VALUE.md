# When a chair benefits from reviewing the combined record

This experiment keeps the first-stage policy from [the selective retry replay](SELECTIVE.md).
After one of two source packets reaches the chair, it can stop, retry the
missing packet, or pay for an ideal review of the combined record. A review
returns its exact archived released score. The chair still has to pay 0.75
points for a retry and successfully deliver the packet to publish the
combined record. Review prices are modeled in the same units as the
70-point documentary rubric. The replay uses existing writer and grading
outputs. It measures the value of a trusted score preview under simulated
delivery.

The [initial protocol](review-protocol.md) fits a chair with three actions.
After inspecting those results, the [residual protocol](residual-review-protocol.md)
holds the direct retry rule fixed and learns whether buying the review
improves return over that specific action. Both use held-family archive
folds and then fit on the archive for replay on exposed Myanmar and
Resolution 2739 conditions.

## Matched archive return

| Policy | Review costs 0.25 | Review costs 0.75 | Review costs 1.50 |
| --- | ---: | ---: | ---: |
| Direct retry, fixed plus-seven | 45.7468 | 45.7468 | 45.7468 |
| Three-action learned policy, greedy | 45.7291 | 45.7799 | 45.7457 |
| Residual learned policy, greedy | 46.5680 | 45.7221 | 45.6974 |
| Residual learned policy, sampled | 46.2195 | 46.0679 | 45.8729 |
| Review if either singleton scores at or below the empty record | 46.6022 | 46.4399 | 46.1965 |

These are exact expected net points, averaged first within families and
then equally across the six archive families. The last row keeps the
same direct fallback as the first. At the 0.75 price it gains 0.6931 points.
It reviews in 32.46% of episodes, blocking a retry in 9.41% and enabling
one in 5.64%. The gain concentrates in Resolution 2422, where it adds
4.3265 points. With that family omitted, its macro gain is −0.0336.
The sampled residual policy gains 0.3211 points at this price and changes
the retry decision in 6.78% of episodes. Its gain also concentrates in
Resolution 2422. The greedy residual buys reviews in 3.29% of episodes
and changes no retry decisions at this price.

Always reviewing earns 46.6190 at the low price. Reviewing when either
singleton scores zero earns 46.2738 at the high price. These fixed
comparisons show that access to a correct combined score can help where
adding information risks failing release. The learned policies trail the
fixed review controls on the archive. The residual fit is an adaptive
development result using already inspected score banks.

On the two exposed transfer cases, the greedy residual and the singleton
rule both skip review and match direct retry at 57.9940 net and 58.4887
released points under matched delivery. The sampled residual buys some
reviews and pays for them without changing any retry decisions. These
cases offer no evidence of a transfer benefit from the review.

## Replay

Run from this directory with Python and NumPy. The JSON artifacts include
both matched and stressed link signals, family-level returns and review
counts. The first script cross-checks exact branch dispatch and tests
gradients and observation boundaries. The second checks its residual
branch values against the first replay.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python review.py | cmp review.json -
python review_residual.py | cmp review-residual.json -
```

[Three-action fit and controls](review.json) · [Residual fit and decision changes](review-residual.json)
