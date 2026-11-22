# Remove the declared relationship bonuses from the native editor

The centered fit falls below fixed standalone scoring when the real relationship bonus is hidden and both answer orders count equally. Its gain in one order disappears under reversal. The evaluator keeps the same true source rubric, delivery rates and priors as the earlier experiment.

The 40 fresh requests on Resolution 2422 retain Peru's two texts, observed Russian notes, public role metadata and standalone values. The prompt replaces its reference to explicit joint bonuses with an instruction to choose a useful grounded comparison. The payload omits the joint requirements. The frozen head was trained on Resolution 2553 with full rubric features. All its evaluation-time relation features are zeroed, and Serbia uses the same standalone rule in all new arms. The lexical comparator receives the same visible texts. [Protocol](protocol.md) · [Exact prompt pairs](plan.json)

| Condition with receipt content | Mean released points |
| --- | ---: |
| Raw single-order model | 50.67352 |
| Two orders, raw mapped average | 50.25000 |
| Frozen fit using raw margins | 50.58891 |
| Frozen fit using centered margins | 50.81172 |
| Frozen fit using the average of both centered orders | 50.84937 |
| Same-input standalone and lexical rules | 51.00000 |
| Earlier fixed rule given the true checklist | 51.30125 |

The single-order centered fit scores **51.22594** in the reversed order and **50.39750** in the canonical order. The fixed standalone score is 51 in both. Averaging the centered margins still falls short, even with twice the current context calls. Under arrival only and under no observation, the centered fit ties standalone at 51. The lexical policy makes the same choices as standalone throughout. The earlier known-checklist result uses additional information and a different prompt, and serves as a ceiling comparison. [Matched policies by order and receipt](scores.json)

Qwen chooses literal B on 39 of 40 calls. The 4B checkpoint processes 13,408 tokens of input and emits 80 readout tokens on NVIDIA RTX PRO 6000 Blackwell Server Edition. The worker exits normally. Inference uses one active call per presented order, with one cached or additional no-observation call for centering that order. The paired centering control was added after inspecting the single-order asymmetry and leaves every earlier measured arm unchanged.

The source-bound scorer and a direct branch dispatcher agree on every reported policy value. This is one exposed docket with authored priorities and simulated receipts. There are no new model updates or prose outputs. [Evidence receipt and checkpoint](evidence/launch.json) · [Verified logits](verified.json)

## Reproduce

From this directory in the project Python environment:

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" collect_masked.py plan | cmp plan.json -
"$py" collect_masked.py verify | cmp verified.json -
"$py" score_masked.py | cmp scores.json -
```
