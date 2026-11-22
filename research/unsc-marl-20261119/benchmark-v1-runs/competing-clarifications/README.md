# Learn whom to ask when either delegate can complete a proof

One question can request one signed compatibility claim. In the
two-opening state, each recipient could establish a joint agreement by
accepting the peer's opening option. Each recipient has a declared
probability of local compatibility and a separate declared delivery
probability. A second state has only one unresolved option and can
end in agreement or impasse. A third state has an existing certificate.
The chair sees the public probabilities and ledger. The responder sees
the sign from its own fictional mandate. The public ledger independently
evaluates each emitted claim.

All 486 synthetic development presentations and 3,072 held presentations
are enumerated. The held grid uses different rates. Iraq and Syria supply
the four package IDs. Their substantive wording is absent from the
features, so the two docket labels produce structurally duplicated
results. This checks generalization across public rate combinations
and channel regimes. It does not establish transfer across independently
observed diplomatic families.
[Locked protocol](protocol.md) · [Fitted weights, expected reward and held actions](results.json)

| Policy | Mean net across modes | Mean net on competing two-opening states |
| --- | ---: | ---: |
| Fixed first proof-relevant recipient | 0.6405 | 0.3524 |
| Delivery-first routing | 0.6661 | 0.4292 |
| Compatibility-first routing | 0.6694 | 0.4390 |
| Learned chair and learned responder | 0.6781 | 0.4650 |
| Learned chair and exact responder | 0.6816 | 0.4756 |
| Probability-product routing | 0.6817 | 0.4759 |
| Exact public-belief planner | 0.6820 | 0.4767 |

Both policies train for 96 CPU updates by differentiating exact expected
team reward. The learned chair inverts its recipient appropriately on
132 of 136 paired conditions where swapping delivery rates switches the
optimal recipient and both actions are queries. Probability-product
routing handles all 136. Signed scope and complete public proof prevent
wrong commitments throughout the modeled grid. The oracle also declines
queries under a few low-value rates where the learned chair still asks.

## Isolate the reply cost

With the learned chair fixed, the exact responder recovers most of the
remaining gap. The initial responder sends all 1,024 reachable negative
answers in the two-opening rows, although those answers cannot complete
a certificate. Training on a 50/50 mixture of learned and forced
recipient actions leaves the greedy held results and all 1,024
avoidable sends unchanged.

Train the same responder features against the sign of the difference
between the exact team rewards for sending and passing, keeping the
original chair fixed. This removes all held reply errors and recovers
0.6816 net, matching the original learned chair paired with the exact
responder. Supported agreement and impasse totals remain unchanged.
The gain is saved send cost. This dependent component fit uses reward
labels from synthetic training branches and no public held labels.
[Forced-recipient protocol](reply-coverage-protocol.md) · [Coverage and reversal audit](reply-coverage.json) · [Counterfactual credit protocol](reply-credit-protocol.md) · [Responder-only results](reply-credit.json)

The first evaluation attempt stopped on a misspelled question-cost
variable. The corrected run uses the same cost in both the fit and
replay. The independent exact planning check bounds every row.
All three fits use simulated dialogue and modeled erasure. No model
inference or language weight updates are involved.

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python study.py | cmp results.json
python reply_coverage.py | cmp reply-coverage.json
python reply_credit.py | cmp reply-credit.json
```
