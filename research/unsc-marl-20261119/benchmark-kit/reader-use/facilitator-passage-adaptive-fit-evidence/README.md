# Refresh the chair's public model of the opening

A 96-update CPU fit recomputes the request and reply features from the current opening policies. The opening agents use their own inventories. The chair uses the observed receipt mask and the public distribution induced by both opening policies. The responder uses its local inventory, its opening action and the heard question. The public distribution is integrated over inventories. Each episode still uses the same private observations and delivery rules as the previous fit.

The new fit's mean soft development return rises from 47.878 to 53.098. Its final mean soft request rate is 0.964. The older static-context fit reaches 53.043. On the two previously examined UN cases excluded from fitting, all 64 greedy opening decisions match the fixed-opening control. The new fit asks in every reachable state. The net table gives expected points above the matched hindsight no-request team.

| Case | Inventory law | Adaptive fit | Prior static joint fit | Fixed-opening fit | Declared planner |
| --- | --- | ---: | ---: | ---: | ---: |
| 2719 | Uniform | +0.696 | +0.696 | +0.696 | +0.950 |
| 2719 | Correlated duplicates | +0.242 | +0.246 | +0.242 | +0.601 |
| 2504 | Uniform | +0.832 | +0.832 | +0.832 | +0.937 |
| 2504 | Correlated duplicates | +0.143 | +0.157 | +0.143 | +0.560 |

The adaptive fit improves stochastic evaluation against the archived static fit with its original context by 0.020–0.024 points per condition. Applying a refreshed context to the archived weights is stronger still in every condition. The fixed-opening fit has the best stochastic score of the fitted teams in all four conditions.

## Change the opening policies after fitting

Hold the documentary reward and channel fixed and give both learned follow-ups the declared planner's opening agents. Recompute features using their actual public opening distribution, or retain the reference opening distribution. In correlated 2719, refreshing moves the archived fit from +0.349 to +0.483 and the adaptive fit from +0.340 to +0.457. In correlated 2504, it moves the archived fit from +0.389 to +0.447 and the adaptive fit from +0.375 to +0.401. The uniform rows tie their stale-context controls. Both learnable follow-ups still ask everywhere. These are greedy component interventions, and the planner still leads in every row.

The result isolates two decisions. Updating the public context can recover some value after opening policies change. The adaptive fit ties the fixed-opening greedy policy here. The request feature uses an expected continuation from a scripted responder. It remains a proxy for the actual advantage of asking over silence.

## Ask only when a question improves on silence

For each reachable receipt, integrate the requester-to-responder delivery over the true opening policy and the frozen responder. Score each legal question against silence including its cost. Choose silence when all question advantages are nonpositive. Choose the request map from the declared channel or, in hindsight, from the measured channel. Score both in the same measured replay.

| Case | Inventory law | Fitted chair | Declared advantage | Hindsight advantage | Declared requests per episode |
| --- | --- | ---: | ---: | ---: | ---: |
| 2719 | Uniform | +0.696 | +0.717 | +0.717 | 0.658 |
| 2719 | Correlated duplicates | +0.242 | +0.412 | +0.412 | 0.467 |
| 2504 | Uniform | +0.832 | +0.849 | +0.873 | 0.658 |
| 2504 | Correlated duplicates | +0.143 | +0.477 | +0.479 | 0.741 |

All numbers in the three score columns use exact hindsight no-request as the reference. The calculation leaves reply actions, opening actions and documentary scoring fixed. It improves the all-ask chair in all four conditions and leaves a 0.083–0.233 point gap to the declared joint planner. On the planner's openings the same request calculation also improves the fitted follow-up, with gains of 0.017–0.051 over the frozen learned chair. [Per-receipt advantages, visits, and chosen maps](silence-counterfactual.json)

## Reproduce

The [pre-run comparison](protocol.md), [training trace and held results](results.json), and [opening intervention](opening-intervention.json) use 30 existing development banks, two inventory laws, and archived admissions on Resolutions 2719 and 2504. Run from the parent directory with NumPy and CPU PyTorch.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_passage_adaptive_fit.py | cmp facilitator-passage-adaptive-fit-evidence/results.json
python facilitator_passage_adaptive_swap.py | cmp facilitator-passage-adaptive-fit-evidence/opening-intervention.json
python facilitator_passage_adaptive_request.py | cmp facilitator-passage-adaptive-fit-evidence/silence-counterfactual.json
```

This experiment scores structured policies under simulated delivery and authored documentary criteria on two previously examined cases. It collected no fresh final records or independent ratings, and updated no language model weights.
