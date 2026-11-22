# Choose a writer review from shared reward

With one extra writer review, the team that always reviews the first
two notes beats a learned selector under both inventory laws. The
learned selector makes exactly the same 20 choices as the optimistic
rule, which assumes each unreviewed candidate could earn 70 points
and reviews the one with the largest resulting net gain.

## Matched comparison

Each fold excludes every writer variant and order of one UN event
family. The learned policy sees the scores for the empty and
singleton records and the public inventory law. Those inputs determine
its four action features. At deployment the team opens only the selected
review and replans with the resulting score. The evaluation replays
ten archived record banks from seven event families under two inventory
laws. Policy gradients use the downstream team return on the other
families. Historical inputs include generated writer records and
authored or verified controls. [Protocol](protocol.md) · [Plan](plan.json) ·
[Fold results](results.json)

| Strategy | Uniform inventory | Correlated inventory |
| --- | ---: | ---: |
| Forward all immediately | 45.88 | 44.74 |
| Uniform random review | 46.04 | 44.93 |
| Predict the review grade with ridge | 47.11 | 45.74 |
| Learn from team return, sample review | 47.73 | 45.85 |
| Learn from team return, greedy review | 48.34 | 46.70 |
| Optimistic utility | 48.34 | 46.70 |
| Best fixed mask on training families | **48.87** | **47.12** |
| Best review in hindsight | 49.20 | 47.36 |

The numbers are expected net points after modeled message costs and
before review fees. The training-selected arm always picks the first
pair, as does the fitted action-identity policy. The greedy feature
policy wins one family, loses one and ties five against that arm under
either law. The win is Myanmar and the loss is climate. Omitting each
family in turn puts the learned minus fixed effect between −0.72 and
+0.09 under uniform inventory and between −0.53 and +0.04 under
correlated inventory.

The learned policy can pay at most 2.45 or 1.96 points for its one extra
review before losing its mean advantage over immediate forwarding.
Omit Resolution 2422 and it already loses by 0.23 or 0.25 points at
a zero review fee. The hindsight advantage over the first-pair rule
averages only 0.32 or 0.24 points. The study isolates the review decision
inside a cooperative pipeline with fixed openings and routing. It
uses exposed records and modeled transport and adds no model calls
or new grades.

## Reproduce

Run from this directory with the project Aurora Qwen environment active.

```bash
set -o pipefail
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python ../one_review.py | cmp ../one-review.json -
python reward_review.py plan | cmp plan.json -
python reward_review.py run | cmp results.json -
```
