# Train the first reply for the final-record reward

Two matched 96-step CPU fits use the original frozen Qwen3.5-4B
features and 144 synthetic training prompts. The 44 Iraq and Syria
prompts remain fit-excluded. The first fit reproduces the archived
decision head's actions. The second substitutes expected released
final points for the decision reward, subtracts communication cost,
and values a successful follow-up at the published attribution
weight. Each held truthful branch replays a reviewed v1.1 final text.
Follow-up text uses the admitted, schema-clarified live declaration
from the earlier run. The first query and recipient stay fixed.
[Matched protocol](protocol.md) · [Action rewards and rubric provenance](reward-table.json)

| First reply policy | New proofs if delivered | Reachable follow-up contexts /4 | Sends /44 | Expected released points | Normalized net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen feature-cache logits | 5 | 1 | 16 | 557.76 | 7.296 |
| Decision-reward feature head | 12 | 2 | 24 | 947.52 | 12.472 |
| Record-reward feature head | 12 | 2 | 32 | 947.52 | 12.192 |
| Decision head with role-local mask | 14 | 2 | 22 | 1,059.52 | 14.142 |
| Record head with role-local mask | 14 | 2 | 30 | 1,059.52 | 13.862 |
| Learned send-or-pass head with verified sign | 14 | 2 | 20 | 1,059.52 | 14.212 |
| Exact verified reply | 16 | 4 | 16 | 1,167.04 | 15.664 |

The new reward changes none of the 188 exact best actions.
It changes eight held actions of the learned head from pass to
truthful negative reply. None creates a proof or recovers
documentary credit. Both unmasked heads produce four false signs,
which the evaluation rejects at the role-local boundary while
charging for sending. Normalized net is released points divided
by 70, minus modeled send and follow-up costs. The fixed first
question cost cancels in the comparison. First and second delivery
are modeled independently at 0.8. Final-text scores reuse the prior same-assistant annotations.
[Proof, coverage and policy traces](results.json)

## Learn when to send a verified sign

Restrict each role to the sign it can verify from its trusted local
card or to passing. Applying the constraint at decoding recovers
two proofs the prior head's top choice would have lost to an invalid
sign. The direct-credit binary fit uses the same record reward,
compute budget and frozen features and saves two sends versus the
masked decision head. It gains 0.070 net with the same coverage.
It still misses two useful agreement replies, one in Iraq and one
in Syria, and sends six replies the exact policy withholds.

The exact responder using the public ledger and typed local truth
remains stronger. The head experiment tests an exposed typed-card
setting and uses zero new Qwen calls or backbone updates. The
learned choices, changes and evidence replay are available per
presentation.
[Factorization protocol](factor-protocol.md) · [Binary fit and controls](factor.json)

## Verify

Use the project's local Qwen environment for the two CPU fits.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python reward_table.py | cmp - reward-table.json
python learn.py | cmp - results.json
python factor.py | cmp - factor.json
```

## Use the signs that are already in the public ledger

A matched fit adds four public observations to the send decision.
They describe whether a proof already exists, whether the queried
option remains unresolved, how many options remain unresolved, and
whether the other delegate accepts the queried package. The fit uses
separate coefficients for affirmative and negative signs. It still
receives only the currently verified local sign and the public
state. The counterfactual reply is used to compute training targets.

| Send policy | New proofs if delivered | Reachable follow-up contexts /4 | Sends /44 | Expected released points | Normalized net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen features | 14 | 2 | 20 | 1,059.52 | 14.212 |
| Public ledger features | 16 | 4 | 16 | 1,167.04 | 15.664 |
| Public ledger plus Qwen features | 16 | 4 | 16 | 1,167.04 | 15.664 |
| Exact verified reply | 16 | 4 | 16 | 1,167.04 | 15.664 |

Both new heads match all 44 exact actions. The ledger input is
invariant across 2,112 package-letter and role-order permutations
of the held prompts. The Qwen features were cached from original
wordings, so the relabeling check applies to the ledger inputs
and the resulting ledger-only policy. The runtime benefits from
typed local cards and has explicit proof state. The language
features add no gain in these two exposed families.
[Ledger protocol](ledger-protocol.md) · [Raw feature observations](ledger-features.json) · [Weights and held actions](ledger-fit.json)

## Compose the complete controller and stress first-sign delivery

At the original 0.8 delivery rate, the ledger-only first responder
composes with the rubric-weighted follow-up and admitted Qwen
declarations to reproduce 1,167.04 expected released points and
3.20 expected follow-up questions. Both are checked against the
prior final-record replay. Keep second delivery at 0.8 and change
first delivery. The learned head still sends all sixteen useful
signs at 0.02, where the exact rule sends none and earns 0.2544
more normalized net. At 0.04, the exact rule sends twelve. The
four deferred cases are the ones with only partial coverage plus
a costly second request after initial success. The exact rule
earns 0.0088 more normalized net. At 0.08 and 0.80 the policies tie.

The stress test preserves archived successful and erased branches
and reweights them on the first link. There are no new model calls
or Qwen updates. The head was fitted with first-link delivery of
at least 0.39. It still needs cost calibration under poor delivery,
even with proof-aware inputs.
[First-link protocol](first-link-protocol.md) · [Delivery and action audit](first-link.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python ledger_features.py | cmp - ledger-features.json
python ledger_fit.py | cmp - ledger-fit.json
python first_link.py | cmp - first-link.json
```
