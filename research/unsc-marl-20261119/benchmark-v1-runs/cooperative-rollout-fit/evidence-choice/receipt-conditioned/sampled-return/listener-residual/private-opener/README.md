# Train with private opening cards and partner-specific evidence links

Training with a privately constrained opener leaves both documentary results unchanged. Changing which partners benefit from each clause repairs one Resolution 2553 decision and lowers the mean on both synthetic evaluation panels.

## Training and controls

The first desk can send only its available clause. The two deciding delegates receive one shared scalar score per simulated exchange and train the same three coefficients. The later desk can see an earlier clause when delivery succeeds. The third desk receives the opening preference distribution through existing forecast features. Each fit uses 96 menus, 150 updates and 14,400 rollouts. One training arm gives the first clause a 50% availability prior. Another varies it among 25%, 50% and 75%. Both give the same per-menu scores as the earlier public-inventory fit on the two 96-menu panels. On the varied panel they beat the fixed priority rule on eight menus, lose on six and tie on 82. [Initial protocol](protocol.md) · [Initial results](results.json)

Resolution 2553 has one link per pair of desks and each desk's two clauses serve different links. In the original synthetic generator, only 14 of the 96 training menus have this structure. The dependent fit makes every menu use different clauses for the two links at each desk. It preserves local and pair scores, announced priors, delivery rates, and simulation budget. Historical values and optimal actions stay outside the optimizer. The case structure informed this generator change after the first result. [Dependent protocol](split-protocol.md) · [Dependent results](split-results.json)

| Policy | Unrestricted varied priors (96) | Separate links (96) | 2553, UK later (12) | 2553, Germany later (12) | 2422 (12) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Forced private opener, varied priors | 12.41163 | 11.56196 | 34.72719 | 34.35050 | 48.83625 |
| Forced private opener, separate links | 12.40433 | 11.53023 | 34.72719 | 34.38956 | 48.83625 |
| Original public-inventory fit | 12.41163 | 11.57172 | 34.72719 | 34.35050 | 48.83625 |
| Fixed receipt priority | 12.34048 | 11.46582 | 34.72719 | 34.35050 | 48.83625 |
| Content ceiling | 12.59611 | 11.78996 | 34.81180 | 34.47625 | 48.83625 |

Synthetic scores are gains over public evidence. Documentary scores are out of 70. At 75% delivery and a 75% probability of the first opening clause, only Belgium changes action, from its funding clause to its inclusion clause. The later German desk makes the same choices. The new release score is **36.26563**, up from **35.79688**, and equals the ceiling in that condition. The policies make the same choices in the other 35 archived conditions. The synthetic losses and three unrepaired UK-later conditions temper the one documentary gain.

The historical families were excluded from optimization and had already been exposed in the project. Delivery and private availability are simulated. The fixed renderer uses archived source clauses and authored priorities. No LLM weight updates or language generations are involved.

## Reproduce

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" private_train.py plan | cmp plan.json -
"$py" private_train.py run | cmp results.json -
"$py" split_relations.py plan | cmp split-plan.json -
"$py" split_relations.py run | cmp split-results.json -
```
