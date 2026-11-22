# Train historical coordination on the final-record score

## Score correction

The previous exact comparator reused an objective that awarded 21
extra points to a complete record. The frozen learned and fixed-policy
rows used released points minus costs. The common-objective replay
recomputes the exact comparator with the same released-point reward
as all other arms. The difference matters on the compact bank, where
70-point records occur. Exact continuation gains 0.1772 to 0.2323 over
exact no-request on that bank. The earlier bonus-objective archive
remains available. [Common-objective audit](objective-audit.json)

## Fit and deployment check

Train the chair and responder jointly on expected net reward from
144 synthetic banks and three inventory laws. The banks vary card
values, jointly supported claims and score ceilings. Resolution 2422
and the 36 separate synthetic evaluation banks are excluded from the
fit. The learned responder conditions on its own evidence inventory,
its opening send and the physical query, using the public chair policy
to infer which receipt states could have caused that query. This fit
updates routing parameters on CPU. It does not update Qwen or collect
new language responses. [Fit protocol](protocol.md) · [Weights and full scores](fit.json)

The fit improves on the archived team in all six 2422 comparisons.
Its hard chair asks on every reached receipt mask with a legal request.
A public deployment check uses the frozen responder and removes one
unhelpful request at a time, recomputing its input distribution for
each candidate change. It can only delete an existing request.

| Record bank | Inventory law | Exact no-request | Best fixed ask | Unpruned fit | Pruned fit | Exact adaptive |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Literal | Uniform | 49.2296 | 49.2500 | 49.2389 | 49.2741 | 49.3257 |
| Literal | Asymmetric | 48.2169 | 48.2290 | 48.2096 | 48.2486 | 48.2968 |
| Literal | Correlated | 47.7818 | 47.8209 | 47.7885 | 47.8233 | 47.8782 |
| Compact | Uniform | 52.8594 | 52.8964 | 53.0156 | 53.0466 | 53.0917 |
| Compact | Asymmetric | 51.6594 | 51.7150 | 51.7492 | 51.7882 | 51.8366 |
| Compact | Correlated | 50.8185 | 50.8878 | 50.8414 | 50.9470 | 51.0013 |

All arms report released points minus the same communication costs.
The fixed asks have optimized responders under the current objective.
On the six historical comparisons, pruning reduces the query rate from
100% to 13.6–38.8% and beats both the strongest fixed ask and exact
no-request. This applies the public model of the held docket during
deployment, so the six rows measure the learned-and-pruned procedure.
The exact adaptive policy remains ahead by 0.045–0.055 net.
Recomputing the reply posterior helps one historical row over deleting
requests with the reply map held fixed.

On 108 synthetic holdouts, the pruned fit beats the best fixed ask in
69 and exact no-request in 81. It improves over the unpruned fit on
all 108 under the modeled rates and rewards, as expected from the
greedy removal rule. The other holdout rows include ties and losses.
All cases retain the published three-slot protocol and known inventory
laws. One exposed event supplies the historical endpoint. The result
has no independent human assessment of the archived prose.
[Pruning protocol](prune-protocol.md) · [All rollout results](pruned.json)

Replay with the original project Python, NumPy and CPU Torch.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
python3 objective.py | cmp - objective-audit.json
python3 joint_fit.py | cmp - fit.json
python3 prune.py | cmp - pruned.json
```

[Four-docket continuation replay](family-replay/README.md) uses only
empty and singleton scores for deployment. A quality-constrained
selector combines the two learned teams with fixed and no-request
controls, improving nine of twelve modeled rows in released points
and net without a drop on the other three.
