# Fit the chair and verified responder on the same language observations

Pair the two possible recipient prompts for each public opening. The
chair chooses one recipient or silence from public evidence and delivery
rates. A language-conditioned responder chooses whether to send. An
exact check derives the sign from its own typed private card and the
public menu. The public ledger uses that claim to certify agreement or
impasse. The fit uses the stored Qwen3.5-4B representations and 96
deterministic CPU updates on 384 synthetic rate presentations. It
excludes all 30 held Iraq and Syria observations and their four
delivery pairings. Delivery is modeled, and several presentations share
the same two underlying workshop menus.
[Protocol](protocol.md) · [Learned weights and every held branch](results.json)

| Controller on 120 held rate presentations | Questions | Unproductive replies | Expected new proofs | Mean net |
| --- | ---: | ---: | ---: | ---: |
| Fixed first recipient and exact reply | 104 | 0 | 36.54 | 0.4538 |
| Delivery-first and exact reply | 104 | 0 | 38.72 | 0.4693 |
| Joint learned team | 104 | 48 | 38.72 | 0.4553 |
| Public-value planner and exact reply | 80 | 0 | 38.72 | 0.4813 |
| Direct-value chair and original learned reply | 80 | 24 | 38.72 | 0.4743 |
| Both policies fitted by direct marginal credit | 80 | 8 | 35.02 | 0.4539 |
| Private-world ceiling | 64 | 0 | 41.76 | 0.5085 |

The public-value planner fits a proof probability to the synthetic
development observations. It combines that probability, the declared
delivery rate and costs when it considers querying. It achieves
the same expected rate of correct decisions as the joint team with
24 fewer questions. Holding the joint reply policy fixed, a direct
regression on each question's value over silence reproduces the public
planner's summary. That isolates the question costs without changing
the number of expected proofs. It gives no evidence of a learned
routing advantage over the matched planner.

The direct reply fit reduces unnecessary sends by 16 at the same
recipient choices. It also drops four potentially certifying agreements,
two in each family. Expected agreements fall from 17.84 to 14.14
while expected impasses hold at 20.88. The learned responder's
blanket cost reduction therefore gives up useful evidence.
[Dependent protocol](credit-protocol.md) · [Marginal credit fits](credit.json) · [Paired audit](audit.json)

The initial grouping check caught merged role rows in the one-recipient
states. The dependent fit also stopped on a malformed tensor mask.
Both were corrected before the verified results. No new model inference
or model backbone updates were made. This comparison measures finite-
action coordination and costs with a verified private card, leaving
free-language outcomes and new-family generalization open.

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python train_team.py | cmp results.json
python credit.py | cmp credit.json
python audit.py | cmp audit.json
```
