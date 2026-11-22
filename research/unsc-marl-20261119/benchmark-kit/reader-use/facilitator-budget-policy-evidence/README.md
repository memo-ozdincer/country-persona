# Train the source-routing team with a word budget

Two new four-policy fits compare an explicit record budget with an unbounded reward. Both use 96 CPU updates, the same 30 prior development reward banks and the same two inventory laws. The budgeted fit uses 70-, 90- and 110-word caps. Note lengths come from two archived development cases and rotate across the source slots in the training augmentation. Fitting assumes perfect message admission and maximizes expected terminal record points less known message costs. For each receipt, the budgeted training reward is the best original score attainable by including a subset of whole notes. The unbounded comparator retains the same subset operation with the limit lifted. [Frozen comparison](protocol.md) · [Loss traces and policy maps](results.json)

The held replay applies existing admission matrices and modeled erasure to two previously examined cases excluded from both fits. Both fitted teams receive the same declared inputs at evaluation. For 2719 the scored reward uses reviewed prefix selection over generic notes. For 2504 it uses authored whole-source scores with the same measured word-length limit. The two endpoints are simulated receipt rewards. The 2719 replay keeps the source-level gate and estimates the word and claim content using a generic note per source.

| Held case | Words | Inventory | Budget fit | Unbounded fit | Declared planner | Hindsight planner |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2719 | 70 | Uniform | −0.223 | −0.223 | −1.402 | +0.125 |
| 2719 | 70 | Correlated duplicates | −0.152 | −0.154 | −2.068 | +0.187 |
| 2719 | 90 | Uniform | +0.141 | +0.141 | +0.093 | +0.245 |
| 2719 | 90 | Correlated duplicates | +0.029 | +0.009 | −0.117 | +0.196 |
| 2719 | 110 | Uniform | +0.189 | +0.189 | −0.146 | +0.388 |
| 2719 | 110 | Correlated duplicates | +0.015 | −0.004 | −0.705 | +0.280 |
| 2504 | 70 | Uniform | −0.094 | −0.094 | +0.108 | +0.108 |
| 2504 | 70 | Correlated duplicates | −0.171 | −0.195 | +0.071 | +0.071 |
| 2504 | 90 or 110 | Uniform | −0.167 | −0.167 | +0.187 | +0.187 |
| 2504 | 90 or 110 | Correlated duplicates | +0.049 | −0.202 | +0.301 | +0.301 |

Scores are net points over the hindsight exact no-request team with the same communication interface. The budgeted fit improves six of twelve rows and ties the other six, with mean gain 0.047 points. Collapsing the identical 2504 90- and 110-word rows reduces the mean gain to 0.032. It beats exact no-request in six of twelve and still asks in every reachable held state. Swapping the fitted continuation alone reproduces the gains. For 2504, direct planning with identical declared inputs beats the new fit in every row. For 2719, the whole-note declaration gives the planner a distorted score landscape and the fit does better under that mismatch. The hindsight alternating planner using the scored bank beats both fits throughout. Alternation provides conditional block optima. [All baseline and component comparisons](results.json)

## Which score assumption changes planning on 2719?

The 70-word whole-note estimate makes every pair infeasible. The reviewed prefix renderer fits pairwise bundles and scores up to 55 overall, versus 49 in the estimate. In a two-by-two diagnostic, replan using whole notes or reviewed prefixes, with or without inferring France's final vote from the unanimous tally. Freeze the scored target, channel and priors across all four alternatives. The two prefix arms use archived review information and serve as hindsight diagnostics.

| Limit and inventory | Whole-note declaration | Whole notes, explicit France vote | Prefixes, infer France vote | Prefixes, explicit France vote |
| --- | ---: | ---: | ---: | ---: |
| 70 uniform | −1.402 | −1.402 | +0.125 | +0.125 |
| 70 correlated duplicates | −2.068 | −2.068 | +0.187 | +0.187 |
| 90 uniform | +0.093 | +0.093 | +0.226 | +0.245 |
| 90 correlated duplicates | −0.117 | −0.117 | +0.165 | +0.196 |
| 110 uniform | −0.146 | −0.146 | +0.374 | +0.388 |
| 110 correlated duplicates | −0.705 | −0.705 | +0.280 | +0.280 |

Prefix feasibility explains the large change at 70 words, even when the planner credits an inferred French final vote. Correcting only that vote criterion in the whole-note model leaves every net unchanged. With prefixes, correcting the vote credit changes results by up to 0.031 points. The planner comparison uses the same underlying source admissions throughout. This isolates the effect of the writing model in two priors on one exposed case. For a prospective test, derive minimum supported excerpt costs from frozen public/source schemas and assess the policy on new cases with independent review and an actual final writer. [All reward banks and replayed policy decisions](belief-audit.json)

## Reproduce

From the parent directory, use the Qwen inference environment with NumPy and CPU PyTorch.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_budget_policy.py | cmp facilitator-budget-policy-evidence/results.json
python facilitator_budget_model_audit.py | cmp facilitator-budget-policy-evidence/belief-audit.json
```

These analyses use the archived notes, authored score banks and same-assistant reviewed spans. They add 192 structured policy updates, zero language model updates and zero new text generations.
