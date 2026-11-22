# Adapt the recipient from unlabeled message history

The previous ranking fit gained on balanced outer-space grid 198 and
lost on the same grid under uniform worlds. This replay freezes the
opener, ranked recipient, fixed recipient, fees and chair verifier.
The recipient sees its own prior cards and delivered peer grades, with
silence recorded when no grade arrives. It has no prior episode
rewards or hidden peer cards. The primary model is told two possible
world mixtures, equally likely at the start of a stationary batch.

We enumerate histories by their exact likelihood ratio under the
two candidate mixtures. All histories with the same ratio have the
same posterior, so their probability mass can be combined. The
deployment turn has a fresh local observation under the same hidden
mixture. Compare a switch between the two frozen recipients, a
public-model planner that uses the inferred posterior for each new
observation, and a planner told the true mixture. The logical
certificate continues to require grade evidence in the current turn.
[History protocol](history-prior-protocol.md) · [Prior data and exact replays](history-prior.json)

## Where the history changes the decision

Results on the affected held grid, averaging balanced and uniform
deployment at the original peer delivery rate:

| History use | Mixture classification | Net |
| --- | ---: | ---: |
| Fixed forecast | — | 0.750750 |
| Always use the rank fit | — | 0.750429 |
| 16 local cards and peer signals | 86.33% | 0.757016 |
| 32 local cards only | 77.81% | 0.755509 |
| 32 local cards and peer signals | 93.85% | 0.758340 |
| Declared mixture, exact best recipient | — | 0.759429 |

The simple switch uses the rank fit when balanced worlds are more
likely. It and the exact posterior planner have the same return to
six decimals on this grid. Adding delivered messages to the same
32 observations closes about 87% of the fixed policy's gap to the
declared-mixture ceiling. In the other three reserve grids, knowing
the mixture changes no available reward. On Myanmar the rank fit
trails fixed under either mixture. Even when the inferred mixture
is often correct, the switch can still choose the inferior
recipient. The public-model planner keeps the fixed score there.
The Mali and Myanmar panels use the canonical package order.

## Vary the delivery rate as well

A second replay crosses both world mixtures with peer delivery of
0.8 or 0.4, holding each unknown regime fixed across the history
and fresh turn. The opener remains frozen at its original action
choices. The recipient tries either all four known candidate regimes
or a narrower model that assumes the nominal link rate. At 16 turns,
the equal-regime mean across reserve grids rises from 0.741054 fixed
to 0.743804 with either planner. The declared-regime ceiling is
0.745393. On grid 198 alone the means are 0.721500, 0.732503 and
0.738857 respectively. Both planners tie in every evaluated panel
despite the narrower planner's wrong link assumption. Joint regime
classification on grid 198 reaches 79.88%. The extra link inference
does not improve the tested actions.
[Delivery-shift protocol](history-link-protocol.md) · [Per-regime outcomes](history-link.json)

These are exact replays over authored grade worlds with known
candidate regimes, a frozen opening rule and stationary histories.
History observations come from scheduled turns and require no probe
messages. Results do not measure the cost or transfer of collecting
such histories in a new negotiation. There are no new language calls,
memo ratings or policy weight updates.
[Preparation correction](history-prior-preparation.md)

## Verify

Use the project Python environment with NumPy and PyTorch.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python history_prior.py | cmp history-prior.json -
python history_link.py | cmp history-link.json -
```
