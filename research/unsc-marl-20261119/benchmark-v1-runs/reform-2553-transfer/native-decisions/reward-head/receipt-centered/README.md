# Center native evidence-choice margins before fitting a shared return

Subtract the editor's no-observation margin under the same answer mapping from its receipt-conditioned margin. Fit three shared coefficients on Resolution 2553 using the exact final-record score. The goal is to use how a receipt changes the editor's preference while reducing the influence of its default answer tendency. A role-matched raw control also uses language only at the desk that can see a receipt. Each fit uses 120 updates and the same planning inputs across both orders. [Protocol](protocol.md) · [Input hashes](plan.json)

## Resolution 2422 transfer

| Fit or rule | Receipt content | Arrival only | No observation |
| --- | ---: | ---: | ---: |
| Raw single-order fitted head | 50.85250 | 50.73953 | 50.71820 |
| Raw single-order, language at the reader only | 50.85250 | 50.73953 | 50.71820 |
| Centered reader with fixed weights | 51.15063 | 50.88719 | 51.03266 |
| Centered reader with fitted weights | 51.30125 | 50.88703 | 50.62203 |
| Earlier paired hybrid | 50.70188 | 50.55125 | 50.40375 |
| Earlier typed-only fit | 51.30125 | 50.69875 | 50.62203 |
| Fixed refreshed policy and exact ceiling | 51.30125 | 51.07531 | 51.03266 |

These are mean released points out of 70 for four held transport and prior conditions in both label orders. The centered fit reaches the content ceiling in all eight matched scenes, recovering **0.44875** points over the raw single-order fit and **0.15063** over fixed weights with the same centering. The existing typed-only fit and refreshed fixed rule already attain the ceiling. In arrival-only and no-observation scenes, the refreshed rule stays ahead. Each policy is independently scored against the source records and simulated receipt outcomes. [All action tables](results.json)

The one-order centered policy uses the later-desk receipt call and a same-mapping no-observation calibration. A cache hit reuses the latter. The third desk uses only the same typed inputs as before. The earlier hybrid averages two calls per deciding desk. This saves modeled reader calls relative to the paired hybrid, while the fixed typed rule uses none. No inference cost or latency data were collected for a fresh deployment.

## Resolution 2721 transfer

Across 24 archived single-order choices, retaining the original runtime tie decisions gives **20/24** correct. Subtracting the absent-receipt margin gives **22/24**, improving the mean source-bound release from 51.76250 to 52.62875. The paired native decoder previously reached **24/24** when its one decision is reused across both orders. Every new fitted head also reaches 24/24 when supplied with the authored clause-pair features. A fixed matching rule with those same features already does so. The two remaining centered text-only errors include one under the opposing lexical cue. The held 2721 prompt differs from the training prompt, and this task has a single active clause choice. It does not establish a gain from shared-return training on text-only selection.

All results use archived logits from exposed historical dockets and exact source-bound rewards. The new experiment updates only the small policy heads.

## Reproduce

From this directory:

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" centered.py plan | cmp plan.json -
"$py" centered.py run | cmp results.json -
```
