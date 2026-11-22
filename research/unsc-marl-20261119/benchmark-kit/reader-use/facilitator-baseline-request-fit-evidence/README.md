# Fit a requester against a fixed no-request team

The fit updates one four-weight chair policy for 96 CPU steps while retaining the learned responder and the opening policies. The outcome objective uses the exact distribution of documentary receipts, the released-record reward and the costs of both requests and sends. Subtracting the no-request team's result within each condition gives the advantage. Penalizing negative advantages adds a downside term to the otherwise baseline-invariant average objective. The 30 development banks, two inventory priors and four training channels give 240 conditions. Training mean advantage moves from −0.090 to +0.286 and mean downside falls from 0.343 to 0.039. [Locked protocol](protocol.md) · [Training trace and policy replays](results.json)

The six evaluation dockets produce 36 event, prior and channel rows. Haiti and Afghanistan share exactly the same declared and normalized observed score arrays, so their simulated results are identical. Deduplicating those score surfaces leaves 30 distinct rows. The table reports those rows and excludes the named Haiti rewrite control. Negative means below the identical no-request team.

| Requester | Mean net gain | Below no request | Mean requests |
| --- | ---: | ---: | ---: |
| Archived robust | 0.0000 | 0/30 | 0.0000 |
| Initial average of clean and degraded estimates | 0.2235 | 10/30 | 0.1948 |
| Analytical degraded estimate | 0.2103 | 8/30 | 0.1161 |
| Fitted | 0.2060 | 8/30 | 0.0802 |
| Exact scores and channel, same responder | 0.2804 | 0/30 | 0.2510 |

The fit captures 73% of the same-responder exact mean gain. It uses 59% fewer requests than the untrained average and 31% fewer than the analytical degraded rule, with slightly lower mean net than either. Net already includes the cost of requests. On source-validated Haiti under clean delivery, the fit gains 0.711 and 0.318 points over no requests across the priors. With topic-asymmetric delivery it loses 0.089 in the correlated-inventory condition. Using the same declared scores with the older Haiti national rewrite makes all six fitted results slightly negative relative to no request. [Per-condition outcomes, costs, and legal request maps](results.json)

## How much would observing the channel help?

For each evaluation docket and prior, hold the responder fixed and enumerate all 864 deterministic request maps. Using the actual reward bank and all three test channels, find the best single map that achieves nonnegative expected advantage in every channel. Also find the highest-mean map without that requirement and the best separate map for each observed channel. This uses hindsight and evaluates the opportunity under the test model.

Across ten distinct score-bank and prior pairs, the best safe single map gains 0.191 on average, and the unrestricted best single map gains 0.235. Observing which channel is active adds 0.045 to the latter number. Thus, channel identification has modest average value on these specific banks, even with ground-truth scores. A hard no-loss requirement imposes a cost, and score-bank differences matter alongside delivery uncertainty. The study does not independently validate the assumed channel probabilities. New evaluations should supply different documentary reward structures and observed replies, including deliberate withheld-evidence controls. The evidence here comes from exposed UN dockets and simulated delivery, and supports a limited requester-training comparison. [Exact map enumeration and replay checks](channel-bound.json)

## Reproduce from the parent directory

```sh
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_baseline_request_fit.py > facilitator-baseline-request-fit-evidence/results.json
python facilitator_baseline_request_bound.py
```
