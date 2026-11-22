# Learn to change requests when evidence priorities change

## Remove the opening shortcut

Repeat the 240-update neural fit with the same score profiles,
initialization and optimizer. Within each group of three synthetic
tasks, hold the opening sends fixed and move the reward bonus
between source pairs. Historical fitting cases retain their declared
openings. The paired fit still produces identical policies on the
held-out fixed-opening pair contrast. It scores 53.671 on the
first-pair task and 52.978 on the last-pair task. The best shared
tail scores 54.437 and 52.377 under those same conditions.
Arithmetic differences across scores can result from changing the
rubric while using the same action table.

## Score individual actions with local expected value

Replace the generic network with a position-shared weight vector
for each of the chair and responder. For each chair request,
compute a public estimate of its incremental value under a fixed
reference reply rule. Also provide the probability the responding
desk can answer and a request cost flag. For each possible reply,
provide the expected marginal value, whether it obeys the heard
request, whether it repeats the desk's first send and whether it
sends anything. Estimate the chair's receipt state from the public
opening plan and the response policy's own observations. Treat a
particular heard request as evidence that its card was missing,
without assuming the responder knows the actual receipt set.

Only the seven weights are learned in the 240-update joint
expected-reward fit. Both policies use masked local actions.
The input reward is the declared rubric. The archived fitting
scores provide the outcome reward, and the same-opening authored
groups supplement the historical fitting samples. Compare the
learned weights with their initial values, the fixed request
script, a constant-valued rubric and exact public planning.

| Fixed-opening scenario | Learned | Initial weights | Constant rubric | Fixed request | Exact tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| First-pair bonus | 54.373 | 53.940 | 53.657 | 54.320 | 54.437 |
| Last-pair bonus | 52.964 | 52.684 | 52.913 | 51.938 | 53.058 |

The fitted action tables now differ on the held-out contrast.
Their mean regret relative to each task's exact tail is 0.079
points. The best policy that uses a single table for both loses
at least 0.340. The value estimates already encode differences
between the public priorities. Comparing initial and fitted weights
measures the additional change from training.

| Historical transfer, net points | Learned | Initial weights | Fixed request | Exact independent | Exact public tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNIFIL, uniform | 54.988 | 54.565 | 54.930 | 53.794 | 55.052 |
| UNIFIL, correlated duplicates | 51.979 | 51.793 | 51.848 | 51.329 | 52.051 |
| Myanmar, uniform | 59.293 | 58.942 | 59.200 | 58.562 | 59.357 |
| Myanmar, correlated duplicates | 56.804 | 56.536 | 56.627 | 56.506 | 56.904 |

These comparisons hold the public-rubric opening fixed across
arms. On UNIFIL and Myanmar, declared and assessed receipt
weights agree. The learned route completes 13.55% of records
on each uniform case, versus 12.53% after erasing the request
at equal cost and 13.21% for the fixed request rule. All policy
scores use the same graded receipt bank and link budget. The
net improvements over fixed requests are 0.058 to 0.176 points.
The learned policy's request costs are higher than the exact
planner's in these cases.

Unreliable receipt weights remain an issue on the modular UNAMA
and emergency-session records, whose actual writer outputs diverge
from declared weights. Improvements over the learned rule's
initialization are small on UNAMA, and the trained route loses
to independence on its correlated inventory prior. Training makes
a small regression on both emergency-session priors relative to
its initialization. The case bank contains previously exposed
records and uses typed-message replay. No new language model
generation or live deliberation has been measured here.

[Paired neural comparison](paired.json) · [Action-level fit and transfers](action-values.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_paired.py
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_action_values.py
```
