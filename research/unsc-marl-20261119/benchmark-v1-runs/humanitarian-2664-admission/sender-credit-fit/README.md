# Resolution 2664 cooperative sender fit

Two desks learn a send policy against archived Qwen3.5-4B terminal release
scores. The terminal score depends on which sources arrive and which one
the chair sees first. The model carrying the learned value is a centralized
critic. At execution each desk receives the same public context and applies
its own send decision.

| Training signal | Oracle choices on 12 held settings | Mean regret in utility points | Extra reward lookups |
| --- | ---: | ---: | ---: |
| Additive terminal critic | 6 | 1.1615 | 0 |
| Pair-aware, with writer orders pooled | 6 | 1.1615 | 0 |
| Pair and writer order from terminal scores | 12 | 0 | 0 |
| Pair and writer order from exact source deletions | 12 | 0 | 20 |

The three terminal critics each fit the same 64 exploratory trajectories.
Ten complete receipt pairs appeared, seven with safeguards first and three
with India first. Pooling those orders estimates a 3.6-point joint benefit
and chooses silence throughout. The order-aware critic estimates zero
joint points for safeguards first and 12 for India first. The two deletion
lookups on each full-receipt trajectory recover the same estimates with
the same training log. The two fits agree on all evaluated decisions.

The send cost is **constructed for this diagnostic**. A send costs its
expected standalone score gain plus two points. The expected gain from
sending both is then 12 times the probability that both arrive in the order
that earned native synthesis, minus four. The exact oracle switches from
neither to both when that gain turns positive. At 85% delivery, for example,
sending both gives utility 26.867 if India goes first 10% of the time and
33.803 if it goes first 90% of the time. Silence gives 30 in either case.
Mean utility is 31.1615 for the order-aware and deletion fits, 30 for
silence, and 29.915 for always sending both. Factual release scores and the
costs used to derive utility are recorded for every action in the results.

The result concerns centralized value learning with known delivery and
writer-order probabilities at execution. The fit is small and exactly
realizable because the critic uses receipt-pair and order features and each
relevant state appears in the log. The chair never generated additional
outputs during training. There is one exposed docket, one exploratory log,
and a cost chosen to make information sharing require a relational gain.
It remains open whether a policy transfers across docket families, works
when writer effectiveness has to be inferred, or improves live diplomatic
deliberation.

```sh
set -o pipefail
OPENBLAS_NUM_THREADS=1 python -B train.py --plan | cmp plan.json -
OPENBLAS_NUM_THREADS=1 python -B train.py | cmp results.json -
```

[Protocol](protocol.md) · [Rollouts, fitted critics and held outcomes](results.json) · [Source of terminal scores](../source-preserving/README.md)
