# Learn questions and replies from a shared outcome

The Mali workshop now has a trained chair and a trained reply policy.
The chair asks a desk or stops. The delegate conditions on its own fictional
requirement and can attempt a truthful sign or stay silent. Disclosed
requirements enter a public proof. Each question costs 0.075 and each
send attempt costs 0.03, including when delivery fails. Both actors learn
from the same documentary reward after costs. The proof rule and reply
format are supplied.

A first joint policy-gradient run collapsed to immediate stopping by update
200. With no evidence delivered, it earned zero in all six held conditions.
The failure is preserved. The second fit exposed actors to randomly sampled
partial states and learned the late turns first. It fit each delegate head
from sampled gains of sending against withholding, then fit the chair head
from sampled gains of asking against stopping. The fit used no action
targets from either exact planner. The redesign changes training exposure
and credit assignment together. [Initial protocol](protocol.md) ·
[Policy-gradient failure and control results](results.json) ·
[Backward training protocol](backward-protocol.md)

| Delivery by desk | Question cap | Joint net | Same chair, always send | Fixed order, always send | Optional-send exact net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.90 / 0.90 / 0.90 | 2 | 0.1305 | 0.1140 | −0.0480 | 0.1380 |
| 0.90 / 0.90 / 0.90 | 3 | 0.4859 | 0.4835 | 0.4626 | 0.5150 |
| 0.90 / 0.80 / 0.35 | 2 | 0.0230 | 0.0110 | −0.0660 | 0.0230 |
| 0.90 / 0.80 / 0.35 | 3 | 0.1016 | 0.0960 | 0.0738 | 0.1444 |
| 0.35 / 0.93 / 0.72 | 2 | 0.0103 | −0.0036 | −0.1449 | 0.0115 |
| 0.35 / 0.93 / 0.72 | 3 | 0.0997 | 0.0923 | −0.0155 | 0.1323 |

Net is normalized documentary credit minus the specified costs, averaged
over all eight hidden worlds and delivery branches. Learned signing
improves net in every matched-chair comparison, with identical mechanical
accuracy. The team reaches 81.0% accuracy at three turns under even
delivery, versus 85.05% for exact planning. On the 0.90 / 0.80 / 0.35
three-turn condition, its accuracy is 40.98% versus 42.30% for fixed
order and 48.95% for the exact net optimizer. The team wins the fixed
comparison on net through lower cost. At two turns, all certified outcomes
are impasses because an agreement requires three disclosed requirements.
One of the asymmetric two-turn cases yields higher recall for the learned
team than for the exact net optimizer because that optimizer can trade
recall for cost. [Fitted weights and decomposed outcomes](backward-results.json)

The one-seed fit uses 46 synthetic menus and excludes all 24 menus
equivalent to Mali under role permutation and value flips. It evaluates
one held menu shape on an exposed diplomatic scenario. Delivery rates are
supplied. Both policies act on typed messages, with no text model fitting.
The saved-weight audit reproduces every held result, permutes roles and
their corresponding rates 36 times, and checks 162 private-observation
contrasts. [Privacy and permutation replay](audit.json)

Run from this directory with Python and NumPy. The deterministic check
used NumPy 2.5.3 and one BLAS thread.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 train.py | cmp - results.json
python3 backward.py | cmp - backward-results.json
python3 audit.py | cmp - audit.json
```

[Matched language witness](language-witness/README.md) keeps the
pivotal reply and skips an optional reply with the same fitted chair.
The frozen writer misses an impasse that the deterministic application
control certifies from the same two public replies.
