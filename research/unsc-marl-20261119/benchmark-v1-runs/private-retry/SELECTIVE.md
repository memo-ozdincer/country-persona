# Price information before fitting the retry decision

The selective policy reaches the priced information ceiling in all
16 Myanmar and Resolution 2739 transfer conditions. A fixed rule
using the same empty-receipt planner reaches that ceiling too.
The learned component concerns the unknown combined-record score
after one packet arrives.

## Exact value of private hints

For each receipt mask, enumerate both desks' deterministic bit maps
from their binary private signals. A delivered desk is silent.
For each possible message vector, the chair picks the best retry
or stops under the posterior induced by that vector. At most 16
pairs of maps are available. Stochastic local maps are mixtures of
deterministic maps, so the exact maximum is a deterministic policy.
The diagnostic optimizer has the true archived score bank and link
law, including the evaluation signal reliability. Independent
branch evaluation verifies the selected rules. Zero fee reproduces
the earlier free-signal bound.

| Cohort and signal condition | Full-bank net without hints | Gain at zero fee | Gain at 0.15 fee | Gain at 0.30 fee |
| --- | ---: | ---: | ---: | ---: |
| Archive, matched | 46.6991 | 0.0523 | 0.0483 | 0.0445 |
| Archive, stressed | 46.6991 | 0.0113 | 0.0095 | 0.0077 |
| Transfer, matched | 57.9287 | 0.0695 | 0.0653 | 0.0612 |
| Transfer, stressed | 57.9287 | 0.0298 | 0.0249 | 0.0200 |

Every positive hint value occurs when neither packet has arrived.
Once the first packet has arrived, hints never change optimal value
on this bank. The exact no-hint archive net is 1.1161 points above
the previous learned system even before any hint gain. Improving
the combined-record estimate has more potential here than fitting
the two hint maps. [Enumeration protocol](hint-bound-protocol.md) ·
[All priced bounds and policies](hint-bound.json)

## Restrict learning to the unresolved combined score

With neither packet received, optimize the hint-and-retry action
from the observed singleton scores. Both the fitted and fixed
policies use the same mean of the two fitting link laws and retain
the .85 signal calibration under stress. The empty-receipt solver
receives a dummy for the unknown combined score and can reach
only a known singleton. With one received, preserve silence from
both hint senders. Train the chair's retry probability using
200 exact CPU updates. The model sees the singleton increments,
baseline and received record's zero-release indicator. The true
joint score supplies terminal reward during fitting.

| Cohort and signal condition | Previous learned policy | Selective learned | Selective fixed |
| --- | ---: | ---: | ---: |
| Archive, matched | 45.5830 | 45.7433 | 45.7468 |
| Archive, stressed | 45.5818 | 45.7020 | 45.7055 |
| Transfer, matched | 57.9189 | **57.9940** | **57.9940** |
| Transfer, stressed | 57.9159 | **57.9536** | **57.9536** |

The fixed comparator chooses its singleton interaction offset on
fitting families only. It uses the same exact first-stage policy.
Both selective policies meet the per-case paid ceiling on the two
transfer families across orders, link laws and signal stress.
The transfer score increase belongs to the shared architecture.
On archive folds the score advantage reverses across families:
the learned rule avoids some climate retry costs and loses on
the Haiti and outer-space conditions compared with the plus-seven
rule. Those differences roughly cancel in the family mean.

These are the same exposed banks and simulated transport protocol.
The architecture was selected after inspecting earlier results.
The hidden combined score is excluded from policy inputs. Evaluation
replaces it with an out-of-range value during the input check and
confirms that the action features stay identical. The scorer
uses both a vectorized return and separate probability enumeration.
[Fit protocol](selective-protocol.md) · [Weights and all replays](selective.json)

## Reproduce

Use the Python environment in the [original study](README.md#reproduce).

```bash
set -o pipefail
"$py" hint_bound.py | cmp hint-bound.json -
"$py" selective.py | cmp selective.json -
```
