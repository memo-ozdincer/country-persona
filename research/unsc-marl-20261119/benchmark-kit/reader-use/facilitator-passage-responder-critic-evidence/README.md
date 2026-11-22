# Value questions by what the learned responder is expected to deliver

The chair uses the public opening distribution, fixed learned responder, message loss and declared admission to predict which receipts each question can produce. It computes the change from silence in material points, probability of a complete record and communication costs. A two-coefficient regression on 712 state-question examples calibrates the material and completion terms. Costs remain exact. The fitted multipliers are 0.9937 and 1.0016. Weighted development RMSE changes from 0.377966 to 0.377745 points. The fitted and unit-weight chair choose identical actions in every evaluation here.

| Passage case with original opening agents | Previous advantage fit | Responder-aware chair | Requests per episode |
| --- | ---: | ---: | ---: |
| 2719 uniform | +0.700 | +0.717 | 0.658 |
| 2719 correlated duplicates | +0.394 | +0.412 | 0.467 |
| 2504 uniform | +0.800 | +0.849 | 0.658 |
| 2504 correlated duplicates | +0.464 | +0.477 | 0.741 |

Scores are net points above fixed-team silence, using measured certificate admissions. The previous fit asks every time in all four rows. The responder-aware chair also beats the previous fit in each of the four rows with planner opening agents. The source of the gain is the prospective receipt calculation, as the fitted correction changes no decision. The analysis verifies that the unit-weight critic equals the independently implemented expected advantage at every receipt and that replay gain equals visitation-weighted advantage. [Pre-run comparison](protocol.md) · [All policy maps and outcome components](results.json)

## Transfer to archived score banks

Four distinct public and scored reward pairs represent UNIFIL, Myanmar, UNAMA and an emergency session. These banks come from previously examined source-reviewed records. This diagnostic assumes ideal admission, since these archives provide final-record scores by receipt and no corresponding measured question-by-source matrix. The responder-aware chair improves six of eight rows over the previous fitted value chair. All four UNIFIL and Myanmar rows reach the fixed-team hindsight optimum. On the other two cases, the public model predicts the same benefits while the achieved record scores differ.

| Archived case and inventory | Previous fit | Responder-aware chair | Case-specific hindsight |
| --- | ---: | ---: | ---: |
| UNAMA uniform | +0.032 | +0.175 | +0.199 |
| UNAMA correlated duplicates | −0.073 | +0.050 | +0.082 |
| Emergency session uniform | +0.046 | −0.030 | +0.167 |
| Emergency session correlated duplicates | +0.053 | −0.005 | +0.131 |

Both cases declare public scores of 34 with no sources and 12 more per source. The archival reviewed bank awards 12 each for sources A and C on UNAMA, and 12 for source B alone for the emergency session. Neither bank awards strict completion. The chair receives the same public rubric, prior and inferred responder behavior across the pair. The current observation therefore induces one policy for both.

Enumerating all 864 legal deterministic maps under each prior gives shared-policy bounds. Using both score banks in hindsight, a maximum-worst-case map obtains at least 0.063 points under uniform inventories and 0.020 under correlated duplicates. The lowest possible worst-case regret for a shared deterministic map is 0.118 and 0.093 respectively. These are two-case bounds under fixed opening and response policies. They provide targets for evaluation of rubric information and calibration. [Exact maps and bounds](reward-alias.json)

## Reproduce

From the parent directory, use the same NumPy and CPU PyTorch environment as the previous fit.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_passage_responder_critic.py | cmp facilitator-passage-responder-critic-evidence/results.json
python facilitator_passage_critic_alias.py | cmp facilitator-passage-responder-critic-evidence/reward-alias.json
```

The calculations use archived cases, simulated transport and authored or source-reviewed score banks. This run supplies routing evidence. It includes zero new model-generated records, independent ratings or language model updates.
