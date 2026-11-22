# Train a chair and responder around the value of remaining silent

Keep the saved budget fit's opening agents fixed. Both continuations train for 96 CPU updates on 180 combinations of development scores, budgets and inventory laws. The matched feature fit updates the existing chair and responder weights. The response-aware chair evaluates every question against silence using the team's current responder distribution and known costs. It integrates over private holdings before execution and uses only the observed receipt at decision time. It learns one additional nonnegative reserve, while the responder learns its four feature coefficients. Both fits optimize the same scored expected reward. Evaluation compiles the chair from the greedy responder that is actually deployed. [Locked protocol](protocol.md) · [Optimization traces and action maps](results.json)

| Policy | Mean requests per episode | Mean net over exact no-request | Wins over exact no-request |
| --- | ---: | ---: | ---: |
| Archived budget fit | 1.000 | −0.051 | 5/12 |
| Continued feature-policy fit | 1.000 | −0.066 | 5/12 |
| Response-aware fit | 0.361 | −0.023 | 7/12 |
| Response-aware chair with archived responder and zero reserve | 0.417 | −0.030 | 7/12 |
| Declared exact joint planner | 0.574 | −0.204 | 8/12 |
| Hindsight exact joint planner | 0.571 | +0.155 | 12/12 |

The response-aware fit beats the continued feature fit in eleven rows, with a mean gain of 0.043 points. It beats the archived fit in seven. The exception to the first comparison is the 2719 correlated-inventory row at 90 words. The initial running count of twelve wins was corrected against the saved row-level results. The learned reserve is 0.002 points and removing it changes no held results. Replacing the trained responder with the archived responder loses 0.0065 points on average, with eight ties, one gain from training and three losses. The larger effect comes from giving the chair a baseline for silence and integrating over the responder's own actions.

For 2466 with ordinary language-mediated admission, the response-aware fit gains +0.106 and +0.120 points over exact no-request under uniform and correlated inventories. Its request rates are 0.603 and 0.786. In the constructed withholding replay it gains +0.008 and loses 0.021 respectively. The declared planner does better on all four 2466 conditions. The large losses for the declared planner in the overall table occur on the 2719 whole-note model, which understates what partial prefixes can assemble. Scored hindsight is an evaluation control with access to the held reward and admission model.

## Fit the responder to exact training action values

A dependent regression learns the value of each legal responder action relative to no-send, under the exact development chair. It uses 8,160 weighted state-action rows from the same development set with 168 distinct score-bank and inventory combinations. It keeps the existing features and recompiles the same silence-relative chair at zero extra reserve. The full-rank regression has 2.558 points of weighted error. It improves seven of twelve rows over the response-aware fit, but loses 0.242 net points on average. [Dependent protocol](responder-regression-protocol.md) · [Fitted regression and replay](responder-regression.json)

The large regressions are in the 70-word 2719 rows. Under uniform inventories the two chairs request at the same rate and exchanging the responder alone reproduces the entire loss, from +0.040 to −1.125 over exact no-request. Under correlated inventories the regression's responder loses 2.062 points when the chair is silent, compared with 0.263 for the response-aware fit's responder. The regression's question map paired with the response-aware responder changes the latter result by only −0.001. This locates the main error in how the responder chooses what to send, including before hearing any question. [Fixed-map swaps](short-budget-swaps.json)

The table averages exposed deterministic replay conditions from cases outside the fitting banks. The evaluation uses prior measured admissions and modeled transport with an exact or authored budget scorer. The 2466 withholding condition is a constructed stress case. This run adds 192 structured-policy optimization updates and one supervised regression. It performs zero language model updates or new text generations.

## Verify

From the parent directory, use the project NumPy and CPU PyTorch environment.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_silence_joint_fit.py | cmp facilitator-silence-joint-evidence/results.json
python facilitator_silence_responder_regression.py | cmp facilitator-silence-joint-evidence/responder-regression.json
python facilitator_silence_policy_swaps.py | cmp facilitator-silence-joint-evidence/short-budget-swaps.json
```
