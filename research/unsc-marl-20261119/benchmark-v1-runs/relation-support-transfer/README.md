# Verify bounded comparisons before rendering them

A frozen Qwen3.5-4B support check, averaged over two label assignments,
accepted **three of four supported comparisons and zero of six unsupported
controls** across the Resolution 2739 reporting and Resolution 2664
safeguards dockets. Both registered comparisons passed the averaged check.
The held 2739 paraphrase fell exactly on the zero threshold.

| Support policy | Supported admitted | Unsupported admitted | Correct /10 |
| --- | ---: | ---: | ---: |
| A means supported | 0/4 | 0/6 | 6 |
| B means supported | 4/4 | 2/6 | 8 |
| Mean mapped logits | 3/4 | 0/6 | 9 |
| Require agreement | 0/4 | 0/6 | 6 |

With B assigned to supported, the two false admissions came from source
removal. Averaging rejected them, along with the unsupported deadline,
reporting rejection, Council consensus, and prior-approval claims. Both
dockets' negative margins were below zero after averaging. The predeclared
cross-docket threshold procedure therefore retained the zero cutoff in both
directions. [Probes and source keys](probes.json) · [Mapped margins and transfer](scores.json)

## What would release

| Canonical record | Fixed facts /70 | Exact-source renderer /70 | Renderer and averaged check /70 |
| --- | ---: | ---: | ---: |
| Resolution 2739 | 56 | 70 | 70 |
| Resolution 2664 | 58 | 70 | 70 |

The model chooses whether to admit an authored candidate for which the
source-pair registry already exists. The renderer requires both exact
source identities and texts and the exact candidate. Removal, altered
text, foreign source IDs, or changed candidate text prevents insertion.
The frozen judge validator checks the exact spans for each composed
70-point record. The added averaging check preserved the registry's
score, taking two forward passes wherever it was used. An exact registry
already reaches the same score without the check, given a trusted
author-reviewed registry.

The two sources together now offer 14 above their standalone points on
2739 and 12 on 2664 in this replay. Normalizing receipts to the registered
pair gives each canonical check one fixed source presentation. This
avoids passing off alternative paraphrases as counterbalanced input
orders for the same candidate. At independent 75% delivery in the prior
cost model, sending both has utility 45.875 on 2739 and 32.75 on 2664,
compared with 42 and 30 for withholding. This is a counterfactual
utility calculation and excludes the gate's inference cost.

The archive contains 20 completed first-token forward judgments on
Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition. Candidate texts,
support labels, and source paraphrases come from assistant review on two
previously exposed dockets. The narrow positive result tests semantic
verification when the candidate is available. It leaves candidate
generation, independent judge validation, scalable registry creation,
and learned deliberation open. The first preparation attempt omitted a
documented Python import path and exited before launching a worker.
[Worker receipt](evidence/launch.json) · [Exact token replay](verified.json)

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B review_transfer.py plan | cmp plan.json -
"$python" -B review_transfer.py verify | cmp verified.json -
"$python" -B score_transfer.py | cmp scores.json -
```
