# Shared-return fitting over native receipt decisions

The fitted hybrid improves on raw Qwen on Resolution 2422. Both
fixed rules reach the documentary ceiling and outperform the hybrid.
Removing the native margins restores the ceiling for both sets of fitted
coefficients when the later desk can read the receipt content.

## Protocol

Fit two three-coefficient residual policies on the four archived
Resolution 2553 conditions in each of three feedback modes. The two
deciding desks share a weight vector and use only their permitted local
observation. Draw the early desk's private availability and all receipt
masks from the stated simulation law. Differentiate the exact team
return through the two stochastic policies. Use 120 CPU updates
per head with a fixed penalty. Compare the same fit with and without
swapped-letter Qwen margins supplied as fixed offsets. Expected
training return above the public contribution rises from 15.1675 to
15.5818 for the hybrid and from 15.1223 to 15.5600 without the offsets.
The greedy hybrid scores 36.2912 on content-visible training conditions,
below raw Qwen at 36.6055 and the refreshed rule at 36.7325.

Freeze the coefficients and 48 request payloads before collecting
Resolution 2422 logits. Russia is the early desk, Peru the reacting desk
and Serbia the independent desk. Cross two early-card priors and two
delivery rates. For every condition, collect absent receipt, both
receipt contents, arrival only, no observation, and independent desk
views under paired answer mappings. The prior and numeric priority
menu are public within the experiment. The early desk is constrained
by its private card. [Protocol](protocol.md) · [Fit trace](fit.json) ·
[Locked requests](plan.json)

## Resolution 2422 results

Mean expected documentary release out of 70 across four equally weighted
conditions. Each row gives the same observation to every arm.

| Observation | Raw Qwen | Hybrid | Fitted without Qwen | Refreshed fixed | Oracle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Receipt content | 41.4038 | 50.7019 | 51.3013 | 51.3013 | 51.3013 |
| Arrival only | 41.4038 | 50.5512 | 50.6988 | 51.0753 | 51.0753 |
| No observation | 41.4038 | 50.4037 | 50.6220 | 51.0327 | 51.0327 |

The hybrid beats raw Qwen in all four content conditions by a mean
9.2981 points. It loses to the same-information fixed rule in two
conditions and ties in two, with a mean deficit of 0.5994. At the .25
staffing prior it selects Peru's second passage for all three receipt
views. The optimum selects that passage only when Russia's matching card
arrives. The fixed policy's mean content advantage over its own
arrival-only condition is 0.2259. The hybrid's is 0.1506. The fitted
typed policy has a larger contrast of 0.6025 because its arrival policy
underperforms the fixed rule.

A post hoc component swap holds each set of coefficients fixed and
removes or adds the Qwen margins. Removing the margins from the
hybrid recovers 51.3013, with the same actions as the independently
fitted typed-only head on all four content conditions. Adding the
margins to the refreshed fixed rule lowers its content mean to
50.5891. The trained coefficients without margins still trail the
fixed rule under arrival-only and no feedback. [Scores and action tables](scores.json) ·
[Component swaps](component-swap.json)

## Evidence and scope

All 48 physical choices prefer literal B, giving zero mapped agreements
out of 24 swapped pairs. The comparisons use the averaged mapped score
margins. The frozen Qwen3.5-4B model reads 18,768 input tokens and emits
96 constrained tokens in 4.09 measured inference seconds, excluding
model load, on NVIDIA RTX PRO 6000 Blackwell Server Edition. The recorded
worker exits normally. The verifier reconstructs every prompt's tokens
and verifies the raw response hashes. The scorer checks 84 transfer
outcomes with the archived source renderer and an independent
expectation calculation. It also reproduces the archived raw decoder
and oracle on all 12 training conditions.

Resolution 2422 is excluded from fitting and previously exposed in
structured evaluations. The native probes are new. Delivery and card
availability are simulated, the payoff terms are authored, and the
evidence menus are source-bound. The fit updates only the six head
coefficients across the two fits. The resulting comparisons measure
bounded evidence selection. Open-ended deliberation, independent judge
agreement and transfer to unseen event families remain unmeasured.
[Verified logits](verified.json) · [Worker receipt](evidence/launch.json) ·
[Evidence hashes](evidence/complete.json)

## Reproduce the archived run

Use the Aurora Python environment linked from the
[parent experiment](../README.md#reproduce) and run from this directory.

```bash
set -o pipefail
sha256sum -c analysis.lock
"$py" reward_head.py fit | cmp fit.json -
"$py" held_native.py plan | cmp plan.json -
"$py" held_native.py verify | cmp verified.json -
"$py" score_held.py | cmp scores.json -
"$py" component_swap.py | cmp component-swap.json -
```
