# Learn when and what to ask from the value of silence

The frozen opening agents and responder come from the prior adaptive fit. A single linear chair predicts the signed net gain of each legal question relative to silence from the existing three public features. The 30 development banks provide 712 reachable question-state examples across two inventory laws. Fitting uses receipt-probability weighting and observed development rewards, with the declared perfect admission model for follow-up. The fitted model has full column rank, 1.768 weighted RMSE and 42% weighted agreement on whether a question helps. It asks in every held episode.

| Case and inventory | Frozen chair | Fitted advantage | Declared calculation | Measured-channel bound |
| --- | ---: | ---: | ---: | ---: |
| 2719 uniform | +0.696 | +0.700 | +0.717 | +0.717 |
| 2719 correlated duplicates | +0.242 | +0.394 | +0.412 | +0.412 |
| 2504 uniform | +0.832 | +0.800 | +0.849 | +0.873 |
| 2504 correlated duplicates | +0.143 | +0.464 | +0.477 | +0.479 |

Rows use fitted openings and measured admission, with net points relative to exact hindsight no-request. The measured-channel bound changes only the chair and uses the measured channel for choosing its action. The declared calculation changes only the chair and uses the public perfect admission model for choosing. It requests in 47–74% of these episodes. The regression improves three of four original-team conditions despite retaining the same overall request rate. With planner openings, it improves three conditions and loses 0.032 in the remaining one. The action maps and receipt-weighted conditional values are available for both sets of teammates. [Fitting protocol](protocol.md) · [All values and maps](results.json)

## Calibrating a higher cutoff

A dependent fit compares 252 cutoffs on development return. It selects 0.268 points, reduces mean requests from 1.000 to 0.995, and gains 0.000257 mean net points over the zero cutoff. Leaving out each authored profile family or archival event in turn produces four ties and two improvements of 0.0013 and 0.0030 after refitting. The final cutoff changes zero held actions under either opening policy. The existing features predict an advantage for a question at every reachable held state, and the development-calibrated cutoff leaves that behavior intact. [Cutoff protocol](cutoff-protocol.md) · [Development folds and held replay](cutoff.json)

The exact calculation confirms how much of the request error can be fixed without changing the other agents. The feature used for the question's expected value assumes a scripted reply, while the counterfactual target depends on what the learned responder sends. The 27 authored training banks use matching public and target scores, and the three archival banks can differ. These two exposed UN cases were excluded from fitting. Delivery is simulated and documentary scoring uses authored criteria. This exercise measures policy routing. It contains no fresh final records or independent review.

Replay from the parent directory using the same NumPy and CPU PyTorch environment as the prior adaptive fit.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_passage_advantage_fit.py | cmp facilitator-passage-advantage-fit-evidence/results.json
python facilitator_passage_advantage_cutoff.py | cmp facilitator-passage-advantage-fit-evidence/cutoff.json
```
