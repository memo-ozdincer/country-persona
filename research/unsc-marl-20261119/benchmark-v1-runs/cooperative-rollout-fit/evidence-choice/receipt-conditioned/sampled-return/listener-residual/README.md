# A listener-specific policy and the Resolution 2553 ceiling

Giving the listening desk its own weight adjustment did not improve the archived documentary score. A separate audit found that one shared weight vector can already attain the exact ceiling in every archived condition.

## Sampled training

Keep the three action features, source renderer, observations and message budget. Fit a three-coefficient adjustment used only by the later desk while continuing to train the shared team base. Both sets of coefficients receive the same terminal advantage. Each arm uses 14,400 simulated exchanges across 150 updates. Disabling the adjustment reproduces the original training trajectory hash, all recorded weights and baselines. [Locked protocol](protocol.md) · [Training and policy replay](results.json)

| Policy | Fresh synthetic, 96 menus | Prior synthetic, 48 menus | Resolution 2553, 24 conditions /70 |
| --- | ---: | ---: | ---: |
| Shared sampled fit | 20.05466 | 20.00748 | 34.53884 |
| Listener adjustment | 20.05047 | 20.00383 | 34.53884 |
| Listener adjustment with receipt content removed | 19.89669 | 19.90542 | 33.94646 |
| Fixed receipt priority | 20.01722 | 19.95636 | 34.53884 |
| Content ceiling | 20.16096 | 20.10766 | 34.64402 |

Synthetic scores are gains over public evidence. The listener adjustment loses on one fresh menu and ties the other 95 against the shared fit. Swapping only the listening desk reproduces that loss. On the prior panel, swapping the other desks reproduces its one loss. On Resolution 2553 the fit, shared control and fixed rule select the same actions in both speaker orders, including the five below-ceiling conditions.

## Representation audit

Enumerating 16 legal plans per condition gives one best plan each on Resolution 2553. Fit linear margin constraints to the resulting 72 listener choices and 24 third-desk choices. The same vector `[1.00000, -0.42643, 0.98523]` selects all 96 actions and releases 34.64402/70. The coefficients respectively weight local priority, joint priority under a uniform partner forecast, and joint priority under a priority-based partner forecast. Positive rescaling preserves the greedy action. The historical witness is fitted to exact answers from the exposed case.

The witness scores 21.41409 on the synthetic training menus and 19.65996 on the fresh menus, compared with 21.77852 and 20.05466 for the sampled shared fit. At the same local coefficient scale as the shared fit, its stochastic training return is 20.46290 versus 21.22956. This rules out a shared-head capacity barrier on the historical conditions and shows a trade-off for the specific witness tested. The next comparison can vary the training forecast and inventory distribution with the shared head held fixed. It remains open whether a policy trained from terminal rewards can reconcile the synthetic and historical results. [Audit protocol](representation-protocol.md) · [All optimal plans and witness scores](representation.json)

The private inventories and channel are simulated, the historic records use an authored source-bound renderer, and the head uses supplied priorities. The experiment adds no model-backbone updates or language generations. Novel UN event families and independent prose ratings remain unmeasured.

## Reproduce

From this directory in the project Python environment:

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
"$py" listener_fit.py plan | cmp plan.json -
"$py" listener_fit.py run | cmp results.json -
"$py" represent.py "$scipy" | cmp representation.json -
```
