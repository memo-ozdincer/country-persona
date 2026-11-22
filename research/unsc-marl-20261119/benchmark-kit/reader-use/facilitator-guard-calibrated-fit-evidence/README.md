# Fit routing against guarded records and calibrate a tied source order

Run three matched 280-update CPU fits. The adaptive fit shares
terminal record reward across the requester and responder. The
material-score arm uses the same training examples, initialization,
receipt distributions and costs. The independent arm uses guarded
scores and the same setup with the query action disabled.

The fitting banks are Outer Space, UNIFIL, Mali, Myanmar and Climate.
They contain previously reviewed records for all eight receipt masks.
Two banks contain whole-record failures under a release guard. UNAMA
stays out of fitting. Every deployment receives the public-only and
three singleton scores of the held-out case. It uses the guarded
singleton scores to order the source slots. Evaluate all tied orders
and give each fitting family equal weight across its admissible orders.
All decisions during replay use the same typed observations and
original link loss and fees. The exact full-table optimizers supply
hindsight ceilings. The comparably informed planners know the
singleton scores and use a summed proxy for unobserved pairs.

| Normalized UNAMA guarded net | Uniform inventories | Correlated duplicate inventories |
| --- | ---: | ---: |
| Archived fit with singleton calibration | 40.224 | 38.840 |
| Material-score fit | 41.335 | 39.453 |
| Guard-aware fit with a live query | 45.556 | 43.694 |
| Guard-aware fit with query erased at equal cost | 46.414 | 45.189 |
| Guard-aware independent fit | 46.457 | 45.232 |
| Exact adaptive planner using singleton estimates | 46.809 | 45.384 |
| Exact adaptive ceiling with the complete reward table | 47.299 | 45.939 |

The guard-aware fit improves over the matched material-score fit
under both priors. Its mean still trails independent delivery. On
UNAMA's original unnormalized records, where only one singleton
and the public-only record pass, the new adaptive fit gets 17.684
under uniform inventories. Optimized independent delivery reaches
42.170.

## Resolve a tied source order with one pair check

In the normalized study, Norway and China each score 46 alone.
Russia alone scores zero after the guard, while the public-only
record scores 34. Reuse one measured pair per probe, in two
separate retrospective treatments. Norway–Russia scores 58.
China–Russia fails the word cap and scores zero. For each treatment,
replace just that pair's proxy value and score the two permissible
slot orderings of the frozen learned table on the proxy. The other
pair scores remain hidden during selection. Apply the same proxy
to an exact independent and an exact query-aware planner.

Either check selects Norway, China, Russia. Its guarded net is
47.208 under uniform inventories and 45.891 under correlated
duplicates. The highest realized return among the equally
informed planners is 46.809 and 45.384, respectively. Retaining the
request in the selected configuration improves over erasure
by 0.794 and 0.703 points. The learned table plus one observed pair
comes within 0.091 and 0.048 points of the corresponding exact
ceilings with the complete reward table.

The one-pair ordering rule was chosen after examining the UNAMA tie.
Both probes reuse archived generations. They demonstrate why this
specific ordering works and motivate a prospective test on a new
family. There are no new language-model generations or live peer
turns in this study. Receipt outcomes use same-assistant review.
[All fit traces and orderings](fit.json) · [Pair-check replay](pair-probe.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_guard_calibrated_fit.py > fit.json
OPENBLAS_NUM_THREADS=1 python facilitator_guard_calibrated_probe.py fit.json
```
