# Forecast how other desks respond to a receipt

The original passage selector forecast each partner from its standalone
priorities. The refreshed forecast first computes the declared fixed
plans, then predicts their choices across possible arrivals. The later
desk uses that prediction for the independent desk. The independent
desk uses a distribution over the later desk's conditional choices.
The planned response depends on announced inventories, delivery rates
and authored claim weights. Realized private availability and actual
actions remain hidden. The simulation gives the forecast to both
fixed and learned selectors before the same message schedule.
[Protocol](protocol.md) · [Locked inputs](plan.json)

## Synthetic fit and holdout

Two decision-making desks share three fitted coefficients. The early
desk's message is forced by the private inventory draw. Exact-gradient
training on 96 synthetic cases raises expected return from 15.36 to
18.95 in 150 updates. The gradient agrees with a finite-difference
check. The 48 holdout cases have a separate seed. A second readout
moves 30% of the announced inventory probability to the next action
while retaining the same actual cases and delivery probabilities.

| Policy | Correct announcement | Shifted announcement |
| --- | ---: | ---: |
| Older fitted selector | 18.6118 | 18.6006 |
| Original fixed priority | 18.5958 | 18.5958 |
| Fixed refreshed forecast | 18.5173 | 18.5602 |
| Fitted refreshed forecast | 18.6521 | 18.6409 |
| Refitted weights with refreshed term removed | 18.5613 | 18.5463 |
| Informed oracle | 18.6669 | 18.6669 |

The new fit averages +0.0403 over the older fit in both matched
readouts. It reaches the oracle in 46 of 48 correctly announced cases
and 45 of 48 shifted cases. The fixed refreshed rule reaches it in 44
and 45 respectively, with larger losses on its remaining cases.
[Training and holdout evidence](results.json)

## Revisit the archival coordination failures

| Archive and order | Original fit below arrival | Refreshed fixed below arrival | Refreshed fit below arrival |
| --- | ---: | ---: | ---: |
| Resolution 2553, UK chooses later | 3/12 | 0/12 | 3/12 |
| Resolution 2553, Germany chooses later | 2/12 | 0/12 | 0/12 |
| Resolution 2422, Peru chooses later | 0/12 | 0/12 | 0/12 |

The refreshed fixed rule reaches the content oracle in all 36
conditions. The fitted version keeps the original high-delivery UK
losses. In the Germany-later conditions it ties the revised fixed
rule, and its improvement survives zeroing the refreshed coefficient.
That improvement therefore comes from the changed coefficients on the
remaining features. The fit cannot claim the full benefit of forecasting
partners. The old outcomes and informed ceilings reproduce exactly.
There are 216 dispatch checks against archived source records.
[Archived policy tables](results.json)

## Give the coordinator a choice of plans

A secondary synthetic replay gives the same expected-return
coordinator three fixed plans, then adds each trained candidate in
turn. The chooser uses the announced inventory prior and the full
configured payoff table. With either learned candidate, mean held
release improves by +0.0379 when the announcement is correct and
+0.0300 under the specified shift. The learned plan is selected in
three and two of 48 cases respectively. Either candidate reaches the
informed ceiling when combined with the fixed plans, and exact
optimization under the announced prior reaches the same ceiling.
The refit adds no benefit to that portfolio over the older trained
candidate. This is an idealized selection test under one simulated
perturbation family.
[Portfolio protocol](portfolio-protocol.md) · [Selections and scores](portfolio.json)

The repaired fixed rule is the stronger archive reference. The learned
candidate helps with part of the synthetic holdout when the coordinator
can inspect an authored payoff model. The experiments test exact
typed simulation on two exposed archives, with no live language
generation or independent score reading. Neither a general learned
advantage nor a transfer claim to unseen negotiations follows.

## Reproduce

Use the Python setup in [the parent experiment](../README.md#reproduce).
From this directory with Bash pipe failure enabled:

```bash
set -o pipefail
"$py" forecast_response.py plan | cmp plan.json -
"$py" forecast_response.py run | cmp results.json -
sha256sum -c portfolio.lock
"$py" portfolio.py | cmp portfolio.json -
```
