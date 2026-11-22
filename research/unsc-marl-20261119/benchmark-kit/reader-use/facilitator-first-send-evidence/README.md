# Isolate the responder's decision when no question arrives

Freeze the openings, the chair's decision map, and the replies to received
questions. Optimize the four existing responder coefficients for 96 CPU
updates using expected team reward in states where the delegate hears no
question. This includes erasures. The 180 development rows and 12 evaluation
conditions reuse the preceding experiment's cases, budgets and priors.
[Protocol](protocol.md) · [Weights, trace and greedy replay](results.json)

| First-send policy | Mean net change from archived | Wins / ties / losses | Mean net over exact no-request |
| --- | ---: | ---: | ---: |
| Archived response-aware fit | 0.000 | 0 / 12 / 0 | −0.023 |
| Fit with the chair frozen | 0.000 | 0 / 12 / 0 | −0.023 |
| Exact under declared whole-note costs and ideal admission | −0.232 | 8 / 2 / 2 | −0.256 |
| Exact with reviewed scores and held admission | +0.058 | 11 / 1 / 0 | +0.035 |

The learned expected development margin rises from 1.986 to 2.012. The
greedy development margin stays at 2.033. No reachable first-send action
changes in any replay condition. The hindsight planner bounds what any
change to this part of the policy can achieve in these replays. It uses
evaluation information and keeps the same openings, question map and
replies to heard questions.

## Decompose the loss at 70 words on Resolution 2719

The public whole-note model gives zero incremental credit for every pair
over its best single note. The reviewed budget model gives 53–55 points
for pairs, up from 47–49 for singles, including the unchanged base of
42. Fix each planner assumption independently after inspecting the losses.
All cells show net change against the archived policy under the same
reviewed scoring and measured channel.

| Planner's budget and admission assumptions | Uniform | Correlated duplicates |
| --- | ---: | ---: |
| Whole notes, ideal admission | −1.430 | −1.569 |
| Whole notes, measured admission | −1.430 | −1.569 |
| Reviewed prefixes, ideal admission | +0.019 | +0.263 |
| Reviewed prefixes, measured admission | +0.019 | +0.263 |

The report isolates the budget assumption in these two rows. The reviewed
prefix costs are evaluation-side annotations. A prospective test would
need to freeze source spans and their costs before running the policies.
The replay uses structured actions and existing admissions. It generates
no fresh diplomatic records and supplies no new evidence of standalone
language-model, persona or deliberation quality.
[Assumption swaps and state mass](budget-disagreement.json)

The first replay attempt failed while computing the first-send diagnostic
for the 64 fine-grained Resolution 2466 receipt masks. The fixed code maps
them to the eight receipt states visible to the chair, as the archived
mediated evaluator already does. Every archived net value is rechecked.

## Reproduce

From the parent directory in the project NumPy and CPU PyTorch environment:

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_first_send_fit.py | cmp facilitator-first-send-evidence/results.json
python facilitator_first_send_budget_disagreement.py | cmp facilitator-first-send-evidence/budget-disagreement.json
```
