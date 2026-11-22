# Condition the chair and responder on the public rubric

The earlier third-send protocol improved full-record completion
and lost net value on partial records. Here every matched arm
starts with the same two sends. A deterministic planner computes
that opening from the declared public rubric and inventory prior
by finding the best independent three-send policy. The adaptive
arms can change the subsequent chair request and the third send.

The chair and responder share a small neural network trained
against expected team return. The static network input includes
the declared receipt-value vector, the public opening plan,
and the inventory prior. At episode time the chair indexes its
table using the received cards. The responder uses only its own
inventory, intended opening send, and heard request. Use the
previous loss, fees and 21-point completion bonus. Train for
240 exact expected-reward updates on three archived case banks
and 27 authored variations of singleton weights and two-source
bonuses, with a uniform fitting prior. All four evaluation
families are excluded from the fit. None of their declared
reward vectors appears in the training vectors.

Keep the same public opening for fixed request, learned request,
exact planning and independent delivery. The exact public tail
computes the best request and response given this opening and
the declared score vector. The hindsight tail uses the archived
assessment scores. The established UNIFIL and Myanmar rubrics
predict all eight assessed receipt scores. On UNAMA and the
emergency-session record, the declared rubric assumes complete
source notes while the reviewed modular outputs withhold some.

| Case, uniform inventories | Conditioned learned net | Fixed query rule | Earlier learned tail, matched opening | Public independent | Exact public tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNIFIL | 54.881 | 54.930 | 54.506 | 53.794 | 55.052 |
| Myanmar | 59.202 | 59.200 | 58.936 | 58.562 | 59.357 |
| UNAMA | 47.371 | 47.397 | 46.857 | 47.439 | 47.662 |
| Emergency session | 40.566 | 40.507 | 40.582 | 40.465 | 40.479 |

On UNIFIL and Myanmar, erasing the query at equal request cost
drops the learned scores by 1.119 and 1.254 points, respectively.
Under correlated duplicate inventories, the learned tail scores
51.816 and 56.606, compared with 51.329 and 56.506 for public
independence. The fixed query rule is slightly higher than the
learned results in three of these four comparisons. Replacing
the numerical reward vector with a constant while keeping the
opening inputs gives identical returns in all eight historical
comparisons. The evidence supports a benefit from the receipt-
aware tail after the public opening. It leaves the learned use
of numerical priorities unproven.

In a post hoc check, infer the available reward from the public-
only and three singleton grades on the two modular writers.
This predicts all unobserved pair and full scores on those banks.
It improves the exact independent planner from 47.439 to 49.163
on uniform UNAMA and from 40.465 to 42.367 on the emergency
docket. It raises the frozen learned tail to 48.027 and 42.144.
Thus the re-estimated source values improve the matched
comparison, while the frozen policy still trails exact
independence. The earlier policy with its original opening
remains a separate reference. No new text generations occur.

As a separate synthetic control, move a 15-point complement
bonus from the first pair to the last pair. Keep the opening,
singleton values, final total and prior fixed. Any tail that
uses the same policy on both tasks loses at least 0.340 net
points on average relative to a task-conditioned optimum.
The learned network produces identical tables on the two tasks.
The opening-plan input can carry enough information for gains
on the historical cases without requiring the learned tail
to respond directly to public values.

[Fit and policy tables](fit.json) · [Matched-opening and singleton audit](audit.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_context.py > fit.json
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_context_audit.py fit.json
```
