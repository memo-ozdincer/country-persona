# Local responder randomization repairs the Resolution 2422 quality loss

The earlier prior-envelope search found no qualifying candidate when the
uniform inventory proxy was used and the Peru–Russia review was seven
points too high. On the held bank that policy released 0.059 fewer rubric
points than the fully informed no-request reference. The new search keeps
the same opening tables, nine forecasts, packet fee, role observations
and v1.4 rubric. It puts the documentary floor directly in the policy
optimization.
[Original replay](../prior-results.json) · [Search protocol](protocol.md)

For each of 864 legal chair maps, a linear program finds the best
forecast net margin under the documentary floor, allowing stochastic
local replies. Of those maps, 44 admit a feasible probability table.
Mixed-integer checks exclude all deterministic tables for those 44 maps.
The relaxation excludes the other 820 maps. None of the four fixed
chair maps can meet the floor, even with stochastic replies. Their best
worst-case forecast quality margin is −0.04151 points.
[Search results](results.json) · [SciPy linear programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html) ·
[SciPy mixed-integer programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

The selected adaptive chair still uses deterministic requests. When the
responder holds all source packets, opened with Russia and hears a request
for Serbia, it returns Peru with probability 0.5412 or Serbia with
probability 0.4588. All other reply choices are deterministic. The
response sampler uses only a fresh local draw and the same private
inventory, prior send and heard query available to the original responder.
The independent delivery replay integrates the sampler's action probabilities
across every inventory and delivery branch. Packet fees are unchanged
from the archived adaptive policy.

| Policy | Held quality over informed silence | Held net over informed fixed |
| --- | ---: | ---: |
| Archived adaptive | −0.0590 | −0.0709 |
| Stochastic adaptive at the floor | +0.0191 | +0.0073 |
| Stochastic fixed, best forecast quality | −0.0290 | −0.0615 |
| Stochastic fixed, best forecast net | −0.0548 | −0.0644 |

The adaptive policy's worst forecast quality margin is zero to the solver
tolerance of 1e-7 points. Its worst forecast net margin against informed
fixed is −0.0144, even though its held net margin is positive.
[Stochastic reply tables and delivery replay](mixed-results.json) ·
[Execution protocol](mixed-protocol.md)

## Conditional policy update across archived settings

Reoptimize a policy family only if its original candidate pool contains
no qualifying policy. Across the 21 distinct settings, the adaptive
fallback qualifies in three settings and keeps the previous choice in
the other 18, including three whose expanded search still finds the
floor infeasible. For fixed targeting, all eight expanded searches
remain infeasible and use the best attainable worst-case quality.

The earlier team falls below informed silence once. The updated team
does so zero times. It wins all 21 against the updated fixed comparator,
which prioritizes quality when the floor is unattainable. Some updated
fixed policies trade net points for released quality. Using the better
net result of the updated and archived fixed comparators in each setting,
the updated team wins 19 and ties two, with a mean gain of 0.120. Against
fully informed fixed routing it wins 17 and loses four, with a mean gain
of 0.059 net points. Its own mean net is essentially unchanged.
[Conditional fallback protocol](fallback-protocol.md) · [All 21 outcomes](fallback-results.json)

These results use one exposed case, frozen authored score banks and a
transport model. They measure a decision policy rather than a new model
fit or independently reviewed deliberation. The first two fallback
reporting attempts failed on an archived-field mismatch and a NumPy
integer JSON conversion. The corrected replay normalizes both without
altering the policy calculations.

## Reproduce

From this directory, use the Aurora Qwen environment and make SciPy
1.18.1 available. The archived run loaded SciPy from the existing
`open-character-20261004-v1` environment after importing NumPy from the
Qwen environment. The scripts run entirely on CPU.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
replay() {
  "$py" -c 'import sys,numpy,runpy; sys.path.append(sys.argv[2]); runpy.run_path(sys.argv[1],run_name="__main__")' "$1" "$scipy_packages"
}
replay solve_floor.py | cmp results.json -
replay mixed_floor.py | cmp mixed-results.json -
replay fallback_audit.py | cmp fallback-results.json -
```
