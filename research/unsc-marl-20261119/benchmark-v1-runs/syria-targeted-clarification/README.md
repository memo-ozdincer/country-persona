# Repair a missing workshop mandate with one question

Frozen Qwen3.5-4B answered a request for its own full fictional mandate.
Collect both possible recipient branches independently from the same
eight archived Syria note pairs. Every reply used valid field/value
JSON and matched the replying speaker's private card. The public ledger
receives the reply and earlier public claims. The private card is
available to the responder and to the evaluator checking reply truth.
The recorded reply replaces that speaker's earlier claims.
[Locked prompts](requests.json) · [Collection protocol](protocol.md) · [Raw replies](evidence/responses.jsonl)

| Replay policy | Questions /8 | Correct dispositions /8 | Wrong commitments | Costed utility |
| --- | ---: | ---: | ---: | ---: |
| Silence | 0 | 2 | 0 | 2.90 |
| Always ask first speaker | 8 | 4 | 1 | 3.13 |
| Always ask second speaker | 8 | 2 | 0 | 2.58 |
| Ask speaker missing a directly stated requirement | 5 | 4 | 1 | 3.25 |
| Learned router | 8 | 4 | 1 | 3.13 |
| Confirm acceptances before committing | 8 | 4 | 0 | 4.28 |
| Confirm acceptances and ask only when a proof can be completed | 2 | 4 | 0 | 4.52 |

The learned router uses nine public features, including which roles
have acceptances or exclusions and whether a certificate is already
present. Its 96 CPU updates optimize expected utility over 400
synthetic states with 8% assumed erasure and a 0.04 question cost.
Its greedy deployment asks in every archived case. It ties fixed-first
routing on decisions and utility. No archived prompt, reply or label
enters training.

One truthful reply recovers each missing impasse in the raw notes.
The projected versions already have enough evidence. In raw
Brazil-first overlap, querying Brazil establishes its compatibility
with A. Combining it with the UK note's earlier false recommendation
would certify A, which conflicts with the UK's real fictional
checkpoint condition. The dependent confirmation check gives
affirmative proof only to complete speaker-bound compatibility
declarations. It retains evidence-backed exclusions and blocks the
wrong recommendation. A public proof-relevance check enumerates the
menu and allowed requirements before deciding whether any answer can
complete a proof. It reduces deployment to two questions, one for
each uncertified impasse. The first-proof-relevant rule reproduces
both selections and all scores. These cases give no evidence the
learned recipient ranking improves the guarded outcome.
[All recorded branches and fit trace](results.json) · [Confirmation protocol](confirmation-protocol.md) · [Runtime decisions](confirmation.json)

Even an oracle choosing among the observed one-question branches
recovers only four of eight exact outcomes. None of the four overlap
records contains both confirmed acceptances within one question.
Combining the two independently recorded replies for each episode
recovers eight of eight. That is a parallel replay of two full
disclosures, with no additional models or observed sequential response.
It isolates the question budget and the initial proof state.
[Two-reply composition](parallel-bound.json)

The 16 inference calls used NVIDIA RTX PRO 6000 Blackwell Server Edition
with zero Qwen updates. The speaker list, role-bound prompts and token
traces replay. The guarded policy is a dependent replay on one exposed
historical family. Its language role uses an explicit narrow field
dictionary and complete-disclosure contract. Deployed transfer and
added value from adaptive learned coordination remain open.
[Launch receipt](evidence/launch.json) · [Verification](verification.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python collect_clarification.py deck | cmp requests.json
python collect_clarification.py verify | cmp verification.json
python route.py | cmp results.json
python parallel_bound.py | cmp parallel-bound.json
python confirm.py | cmp confirmation.json
```
