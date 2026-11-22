# Transfer the stochastic responder to five archived UN cases

Resolution 2422 motivated a stochastic reply when the original policy
catalog cannot meet its expected documentary floor. This audit applies
that rule to five different, previously scored cases. Myanmar, UNIFIL,
UNAMA and the emergency special session come from the historical
information frontier. Somalia uses the archived bank whose numeric
message IDs were normalized after generation. The grades were fixed
before the audit. This CPU test reuses the existing generated or
assembled documents and their same-assistant grades.
[Protocol](protocol.md) · [Locked case banks](plan.json)

Each case contributes 18 combinations of inventory mixture, prior
announcement and error on the reviewed two-card grade. The router sees
seven grades and infers the eighth. All policies share the same
information, openings, legal responder actions and modeled fees.
The strongest matched fixed comparator is the larger held net of the
original fixed policy and the updated fixed policy. The fully informed
fixed comparator also sees the true mixture and full score bank.

| Adaptive policy | Wins / ties / losses vs matched fixed | Mean net gain vs matched fixed | Wins / ties / losses vs informed fixed | Quality below informed silence |
| --- | ---: | ---: | ---: | ---: |
| Original deterministic catalog | 77 / 10 / 3 | +0.096 | 68 / 1 / 21 | 10 / 90 |
| Conditional exhaustive deterministic search | 79 / 9 / 2 | +0.102 | 69 / 1 / 20 | 10 / 90 |
| Conditional stochastic search | 79 / 9 / 2 | +0.100 | 68 / 1 / 21 | 10 / 90 |

The original adaptive catalog has no qualifying policy in 26 rows.
Expanding the search qualifies two Somalia rows with deterministic
replies. It also qualifies one Myanmar row that requires randomization
to meet all forecasts. In that Myanmar row, randomization lowers held
net by 0.156 points and reduces held released quality by 0.119 points.
Both policies remain above the no-request reference in that row. The remaining 23 rows are
infeasible even with local stochastic replies. The expanded fixed
family qualifies in zero of its 34 searches.
[Full replay and selected policies](results.json)

## Quality fallback and the value of an accurate review

Directly minimizing the worst forecast quality shortfall changes all 23
infeasible rows. Held quality improves in 11, ties in 10 and declines
in two. Mean held quality rises by 0.014 points across those rows, while
greater message cost lowers mean net by 0.012. The total count below
informed silence moves from 10 to 11. Improving the forecast objective
therefore fails to repair the held quality floor.
[Shortfall protocol](shortfall-protocol.md) · [Exact policy and delivery replay](shortfall-results.json)

An exact-repeat-review counterfactual takes each of the same 23 rows
and substitutes its already recorded clean-grade condition, holding
the opening tables and prior announcement fixed. Twelve triggered rows
already have a clean grade. In the 23 pairs, all 10 held documentary
regressions disappear, 10 net results improve and 13 tie. Mean net
gain per triggered review is 0.046 points before review cost. This
diagnostic assumes the second reading yields the exact grade. The run
uses archived results and measures neither a real judge's correction
rate nor a review cost.
[Paired review calculation](review_value.py) · [Paired outcomes](review-value.json)

## Replay

Run in the same CPU environment as the earlier search. The first
preflight accidentally passed the SciPy directory as the mode. The
corrected wrapper removes it before handing arguments to the script.
The first shortfall attempt collided with an archived module named
`transfer`. The corrected script loads its dependency by file path
under a separate module name.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
replay() {
  "$py" -c 'import sys,numpy,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path(sys.argv.pop(1),run_name="__main__")' "$scipy_packages" "$@"
}
replay transfer.py plan | cmp plan.json -
replay transfer.py run | cmp results.json -
replay shortfall.py | cmp shortfall-results.json -
python3 review_value.py | cmp review-value.json -
```
