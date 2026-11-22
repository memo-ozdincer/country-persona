# Fit the reviewer before the proposer

Staging the two fits increases requests without changing a held
judgment. It also leaves the reviewer unable to use a helpful second
read in cases where the correct relation is available as a legal reply.

Use the same 19 archive claims, eight Myanmar claims, model reads,
actions, payoff and 0.10 query cost as the joint fit. Optimize the
reviewer on both query branches before fitting the proposer against
its frozen greedy decisions. Each head gets 160 CPU updates, matching
the original per-head count. Staging uses separate optimization
passes. Each archive fold excludes its whole event family from both
passes. No archive family shares the Myanmar event. The action returns
come from observed Qwen reads and the existing authored scope keys.
[Staged protocol](staged-protocol.md) · [Locked inputs](staged-plan.json)

| Arm | Archive net | Archive extra reads | Myanmar net | Myanmar extra reads |
| --- | ---: | ---: | ---: | ---: |
| Staged fit | 0.3354 | 0.9375 | 0.5250 | 1.000 |
| Original joint fit | 0.3908 | 0.3833 | 0.6125 | 0.125 |
| First read alone | 0.4292 | 0 | 0.6250 | 0 |
| Fixed confidence rule selected on fitting families | 0.2063 | 0.1458 | 0.7250 | 0.250 |

Every staged or joint held prediction equals the first read alone.
The component swaps reproduce the request count of the proposer
and keep each held judgment the same. The staged Myanmar proposer
samples to 0.5214 net with the frozen greedy reviewer. On the full
fitting families, reviewer expected payoff improves from 0.0677 to
0.4572 under uniform querying. Training payoff of the proposer with
that reviewer rises from 0.2967 to 0.4163. These training objectives
describe different stages and use different action distributions.
[Weights, held cases and swaps](staged-results.json)

## Locate the lost correction

Compare both query branches with the better of acting on the first
read and withholding without paying. Give a diagnostic oracle the
true per-case returns. With either fitted reviewer frozen, no
available query strictly improves on that no-query choice on any of
the 27 held rows. Its best net on Myanmar is 0.625. With hindsight
over the reviewer's **existing legal replies**, the paid read can
help on four of 19 archival rows and two of eight Myanmar rows. The
Myanmar ceiling becomes 0.85. Thus the recorded channel contains
usable corrections that the fitted reviewers leave unused.

On Myanmar's presidency claim, both possible second reads can
supply the correct support. One second read can also correct the
false claim that India voted in favour. Both frozen reviewers
defer in the useful branches. On Russia's proposed final extension
of Mali sanctions, the first read returns an incorrect contradiction.
A fitted reviewer can defer after buying one check, costing 0.10.
Withholding immediately costs zero. The archive has a legal
corrective reply worth 0.90 after query cost. This identifies the
missing behavior more specifically than a count of insufficient
queries. [Counterfactual reply payoffs](credit-audit.json)

The study adds no model calls. The event families and their
classification keys are exposed, and contact costs are modeled.
The diagnostic ceilings use hindsight and do not represent deployable
policies.

## Reproduce

Use the Python environment and repository paths from
[the label-mapping study](README.md#reproduce).

```bash
set -o pipefail
"$py" staged_route.py plan | cmp staged-plan.json -
"$py" staged_route.py run | cmp staged-results.json -
"$py" credit_audit.py | cmp credit-audit.json -
```
