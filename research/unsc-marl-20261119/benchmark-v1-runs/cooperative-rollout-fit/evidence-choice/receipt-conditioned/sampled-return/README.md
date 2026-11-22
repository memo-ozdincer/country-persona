# Learn which evidence to send from a single team score

Three delegates use a shared three-coefficient policy to pick source clauses. The later delegate can see the earlier delivered clause. A fixed renderer scores the chair's final record after delivery. Each of the 150 updates uses one sampled delivery mask, set of delegate choices and final score per training menu. The two sampled arms each receive 14,400 scalar returns. They use paired draws and a baseline computed from previous rewards. The gradient is the terminal advantage times the sum of the delegates' action log-probability gradients. [Protocol](protocol.md) · [REINFORCE](https://doi.org/10.1007/BF00992696)

| Policy | Released gain over public evidence, 48 synthetic menus | Released points /70, 24 Resolution 2553 conditions |
| --- | ---: | ---: |
| Sampled return, content visible | 20.00748 | 34.53884 |
| Sampled return, no receipt visibility | 19.90542 | 34.02068 |
| Sampled content weights, receipt visibility removed at evaluation | 19.90906 | 34.02068 |
| Enumerated gradient, content visible | 20.00748 | 34.53884 |
| Fixed priority, content visible | 19.95636 | 34.53884 |
| Fixed priority, no receipt visibility | 19.83068 | 34.10776 |
| Content ceiling | 20.10766 | 34.64402 |

The sampled and enumerated content policies have identical scores on all 48 synthetic menus and all 24 Resolution 2553 conditions. Access to the delivered clause adds 0.10206 points over separately trained open-loop weights and 0.09842 over removing visibility from the trained content policy. Against the equally informed fixed priority rule, the learned team wins five synthetic menus, loses four and ties 39. A diagnostic swap keeps the later desk fixed and uses the fitted earlier and third desks. Its synthetic mean is 20.05160. The reciprocal swap scores 19.90722. These are post-fit comparisons with the same message budget and scorer.

On Resolution 2553, all three content-aware policies tie per condition. The learned content policy scores 34.72719 with the UK later and 34.35050 with Germany later. Five conditions fall below the content ceiling. An exact swap of the later desk closes all three UK-later gaps. Swapping only the third desk, Belgium, closes both Germany-later gaps. The opener is forced by its fictional private inventory in this transfer. The role audit recomputes both content policies from the source-bound records using independent mask probabilities. [Full transfer policies and training traces](results.json) · [Role audit](role-audit.json)

The optimizer sees authored local and joint priorities as features. It receives one aggregate outcome per simulated exchange. A finite-difference check using one enumerated menu agrees with the expected sampled update to within 1.4e-10 across three baselines. Resolution 2553 is excluded from the optimizer and publicly exposed in this project. This study measures source selection with modeled delivery and a fixed writer. It leaves language generation, independent judging, and transfer to a sealed event family unmeasured. No LLM weights changed. [Gradient check](gradient.json)

The first plan-only attempts hit import collisions among nested legacy modules. Loading the 2553 integration under a unique module name and supplying the repository's established Python paths repaired the imports before training. No rewards were sampled before the successful run.

## Reproduce

From this directory in the repository's [Aurora Python environment](../../../README.md#replay):

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" sampled_team.py plan | cmp plan.json -
"$py" sampled_team.py run | cmp results.json -
"$py" verify_gradient.py | cmp gradient.json -
"$py" audit_roles.py | cmp role-audit.json -
```
