# Transfer opening-delivery values between UN dockets

The factored sender matches the content-aware oracle on all **576**
canonical settings across three held dockets. It uses the expected
standalone value, the change in reply value and the possible
relationship credit. The same formula with the full rubric bonus
and zero fitting makes identical decisions. The fit learns a
relationship fraction of **1.0** in all three folds. The payoff
structure and source checks account for the canonical result.

| Held docket and prices | Raw value transfer | Factored transfer | Unfitted rubric formula | Best arrival-only |
| --- | ---: | ---: | ---: | ---: |
| 2664, original | 37.565 | 37.630 | 37.630 | 37.630 |
| 2664, lower | 39.166 | 40.316 | 40.316 | 40.316 |
| 2739, original | 37.114 | 37.772 | 37.772 | 37.772 |
| 2739, lower | 39.693 | 40.084 | 40.084 | 39.724 |
| 2744, original | 39.245 | 40.565 | 40.565 | 39.457 |
| 2744, lower | 45.950 | 47.230 | 47.230 | 45.528 |

Each fold measures 24 forced terminal outcomes in the other two
families. The raw fit pools delivery advantages by expected
relationship compatibility. It matches the oracle in 222 of 576
cases. The factored fit subtracts the declared standalone and reply
value differences before estimating the fraction of the relationship
points retained. Each published option weight and relation tag is
available for the target. This is a strong assumption about the
quality and visibility of the local scoring contract.

The factored sender takes the original-price 2739 mean send cost
from the earlier frozen transfer's 5.400 to 0.717. It raises utility
from 35.958 to 37.772 under the same fixed receiver. That ties
arrival-only. The lower-price effect reaches 40.084 versus 39.724.
The no-relationship rule reaches 38.710 there, showing the value of
including the relationship opportunity in the sending budget. The
best-response oracle reads the target outcome table. None of those
outcomes enters the fit or the decision threshold.

The held 2739 objection paraphrase still causes a false positive in
the averaged verifier. At lower prices the factored sender then
scores **35.457 versus 39.700** for arrival-only and matches the
oracle in two of 96 settings. The split verifier rejects that false
positive and restores the canonical scores. A learned marginal
value from clean donor outcomes cannot compensate for the wrong
target observation. Its confidence in the relationship also
increases the cost of that mistake.

The cases and terminal records come from previous exposed docket
work. The family holdout separates sender fitting from evaluation
of the outgoing decision. The receiver contract and local rubric
features are supplied. The experiment uses cached records and
verifier outputs, one fixed set of deterministic paired queries,
and no new model calls. It measures transfer in a documentary
simulator. Independent record quality and unseen family transfer
remain open.

[Protocol](protocol.md) · [Locked folds and inputs](plan.json) ·
[Calibration logs, decisions and stress tests](results.json)

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B study.py --plan | cmp plan.json -
python -B study.py | cmp results.json -
```
