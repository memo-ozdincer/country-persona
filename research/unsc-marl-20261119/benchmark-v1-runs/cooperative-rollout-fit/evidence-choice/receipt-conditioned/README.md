# Choose evidence after seeing the first delivered note

The later desk conditions its choice on the exact earlier note that
reaches the chair. It sees an empty observation when that note fails
delivery. Its own delivery and the third desk's note remain hidden.
This gives the role a way to defer a complementary claim until it
knows the matching claim is present. The simulator uses the same
delivery event for the observed note and the final record. It treats
the receipt broadcast as free.
[Protocol](protocol.md) · [Locked setup](plan.json)

The three shared coefficients are fitted by exact policy gradients
from documentary reward. The training set has 96 synthetic cases.
The 150 updates move expected training return from 15.15 to 21.23.
A finite-difference check validates the gradient. Reproducing the
no-receipt objective, gradient and held outcomes against the previous
implementation verifies the open-loop comparison.

| Policy on 48 synthetic holdout cases | Mean released points above public lead | Ties with adaptive oracle |
| --- | ---: | ---: |
| Earlier fitted open loop | 19.9536 | 35 |
| New weights with receipt removed | 19.9536 | 35 |
| Fixed priority, arrival flag only | 19.9194 | 40 |
| Fixed priority, exact message | 19.9564 | 41 |
| Fitted selector, exact message | 20.0075 | 42 |
| Informed static oracle | 20.0101 | 39 |
| Informed adaptive oracle | 20.1077 | 48 |

Against the equally informed fixed rule, the fitted policy wins five,
ties 39 and loses four, averaging +0.0511 points. Against the earlier
fitted open loop it wins 11, ties 34 and loses three, averaging +0.0539.
With the receipt removed its mean returns to the earlier baseline.
Across 48 scenarios the learned adaptive policy comes close to the
informed static ceiling, with adaptive planning still ahead.
[Training curves, policy tables and held results](results.json)

## Archived UN results

On Resolution 2422, both the fixed and learned receipt-conditioned
policies choose Peru's cooperative passage unless Russia's matching
staffing passage has arrived. If the note arrives, Peru's call for
Council unity earns joint coverage. The fitted and fixed adaptive
policies reach the adaptive ceiling at all four delivery rates.

| Independent receipt probability | Best static release | Adaptive release | Gain |
| --- | ---: | ---: | ---: |
| 0.35 | 41.4000 | 41.5225 | +0.1225 |
| 0.55 | 46.2000 | 46.5025 | +0.3025 |
| 0.75 | 51.1875 | 51.5625 | +0.3750 |
| 0.95 | 56.6075 | 56.7025 | +0.0950 |

On Resolution 2475, the local priority and every tested policy tie
at all four rates. The previous France evidence omission is already
resolved by the authored passage values. For both archives the
independent source renderers verify 208 distinct selection-and-receipt
records against the simulation at every rate.
[Archived choices and exact scores](results.json)

## Make the earlier passage private

A known deterministic sender can make arrival alone sufficient to
infer its passage. To test the contents, give Russia exactly one
available passage in a fictional private draw. The role cannot choose
the other passage. Peru knows the probability of staffing versus
medical evidence and sees only the assigned signal. The experiment
crosses three staffing priors with four independent receipt rates.
Neither fit uses these new conditions.

The content-aware learned and fixed policies both equal the content
oracle in all 12 conditions. They beat the strongest arrival-only
policy by 0.031–0.451 expected points. The independent check gives
the content value as p² × [s − max(0, 3s − 2)], where p is the common
receipt probability and s is the staffing probability. It matches
all 12 rendered evaluations. For example, at 0.75 receipt and equal
prior odds, reading the passage rather than just receiving the
arrival signal adds 0.28125 expected points.
[Private receipt protocol](private-protocol.md) · [Private-condition results](private-results.json)

These experiments establish a concrete benefit from the observation
in a simulated UN source task. The strongest equally informed fixed
policy realizes the same observed benefit on the archived cases.
The small synthetic gain from learning needs external validation.
The role features and private variant are authored, the benchmark
release is fixed, and no language model weights were fitted.

## Reproduce

Use the identical Python variables from the
[parent reproduction guide](../README.md#reproduce). Run here with
Bash pipe failure enabled.

```bash
set -o pipefail
"$py" receipt_choice.py plan | cmp plan.json -
"$py" receipt_choice.py run | cmp results.json -
"$py" private_receipt.py plan | cmp private-plan.json -
"$py" private_receipt.py run | cmp private-results.json -
```
