# Learn the hidden value of combining source receipts

The team recovers the exact evidence-selection ceiling on Resolution 2422 after 256 simulated final scores. It gets within 0.009 points of the ceiling in both Resolution 2553 speaker orders. The learner receives only those scores and the IDs of the source clauses that arrived. It knows standalone scores and the channel law. It never receives the true relationship table.

The earlier desk has one privately available clause. The later desk can react to its delivered content, and the third desk chooses independently of the current receipt. During exploratory training both deciding desks choose at random. Subtract the known public and standalone points from each observed score. Fit a ridge model over all 12 possible pair features. The matched receipt-lookup control sees the same outcomes and additive fallback, but learns a separate adjustment per exact receipt. The planner then selects the feasible role-local policies with the highest expected fitted score. [Protocol](protocol.md) · [Input hashes](plan.json)

| Docket and order | Standalone | Learned pair, 64 scores | Learned pair, 256 scores | Receipt lookup, 256 scores | Full-information static | Full-information content |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2422 | 48.81818 | 48.99138 | 49.06903 | 49.04806 | 48.83006 | 49.06903 |
| 2553, UK later | 34.93750 | 34.98823 | 35.02892 | 35.02356 | 34.93750 | 35.03723 |
| 2553, Germany later | 33.68324 | 34.59626 | 34.68623 | 34.64034 | 34.08955 | 34.68665 |

Each entry averages 11 deployment conditions outside the exact collection condition and 256 reproducible simulated histories. The reported budgets are the scores available to each individual fit. At a budget of 256, the pair estimator chooses a ceiling policy in **100%, 88.17%, and 99.96%** of the paired history/condition rows. Lookup sometimes estimates the absolute reward table more accurately at that budget. The pair estimator still has a better mean policy return in these banks. With only four or 16 rewards, the UK-later fit can underperform standalone. [Learning curves and exact dispatcher checks](results.json)

## Target under-observed receipt combinations

A dependent test chooses an exploratory policy based on the predicted information in its receipts. It uses the covariance of the pair features from earlier receipts and the known transport law. Standalone credit breaks selection ties. Actual terminal scores only enter the same later reward fit. The comparison shares availability and delivery draws with uniform exploration.

| Docket | Uniform exploration, 64 scores | Information-based exploration, 64 scores | Difference |
| --- | ---: | ---: | ---: |
| 2422 | 49.00143 | 49.03281 | +0.03138 |
| 2553, UK later | 34.98908 | 35.00176 | +0.01268 |
| 2553, Germany later | 34.60754 | 34.64625 | +0.03871 |

At 64 scores the receipt-design policy also reduces mean reward-table error on all three banks. It trails uniform exploration after four scores in two banks and converges to nearly identical deployment scores by 256. The earlier sample count remains important, and this is one fixed comparison. [Dependent protocol](exploration-protocol.md) · [Exploration and deployment results](exploration.json)

The terminal scorer is deterministic, with source-bound authored records and actual reward structure representable by pairwise features. The learner fits each docket/order independently. The result tests learning omitted reward structure and transferring to different delivery conditions within the same docket. It does not measure natural-language inference of relationships, language-model training, robustness to prose judges, or transfer to unseen events.

## Reproduce

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" fit_reward.py plan | cmp plan.json -
"$py" fit_reward.py run | cmp results.json -
"$py" exploration.py | cmp exploration.json -
```
