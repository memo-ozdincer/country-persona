# Update the native Qwen signed-reply policy

Fit rank-four LoRA adapters to the query and value projections in Qwen3.5-4B's
full-attention layers 27 and 31. The 114,688 adapter elements receive 12
updates per run, with one exposure to each of 144 synthetic prompts.
The 44 held Iraq and Syria presentations are excluded from fitting.
The first objective maximizes exact expected team utility across the
three native action tokens. A 0.02 KL penalty anchors to the matched
frozen model. The dependent fit keeps the prompts, shuffle, minibatches,
seed, rank, learning rate and KL penalty. It replaces expected utility
maximization with class-balanced training on the best action under
the same team reward.
[Reward protocol](protocol.md) · [Dependent credit protocol](credit-protocol.md)

| Reply policy | Truthful proof-capable replies /16 opportunities | False replies /44 | Mean held utility |
| --- | ---: | ---: | ---: |
| Matched frozen native model | 6 | 0 | 0.3049 |
| Native expected-reward adapter | 1 | 0 | 0.2387 |
| Native direct-credit adapter | 6 | 0 | 0.3105 |
| Older feature head, raw | 12 | 4 | 0.2891 |
| Exact verified action | 16 | 0 | 0.4618 |

Expected reward alone teaches passing at the expense of useful
communication. Direct credit preserves the frozen model's six
proof-capable replies and saves communication cost in the unweighted
forced-recipient comparison. It trades one proof opportunity from
Syria for one in Iraq. The matched fresh frozen run produces six
proof-capable replies. The earlier frozen feature capture produces
five. The prompt tokens are the same and the batching differs.
All native comparisons use the fresh matched baseline.
[Matched native scores](results.json) · [Matched direct-credit scores](credit-results.json)

## Replay with the same chair

Use the same prior public-value planner and recorded recipient choices
on the 120 rate presentations. Replay each model's selected sign and the
local typed-sign rejection check. Both native adapters send zero false
claims here, so the check leaves their decisions unchanged.

| Responder under the fixed public planner | Expected proofs | Sends | Mean net |
| --- | ---: | ---: | ---: |
| Matched frozen native model | 14.90 | 30 | 0.3201 |
| Native expected-reward adapter | 2.61 | 4 | 0.2407 |
| Native direct-credit adapter | 14.14 | 24 | 0.3165 |
| Older feature head with local check | 29.80 | 44 | 0.4216 |
| Exact verified responder | 38.72 | 56 | 0.4813 |

The small direct-credit gain in the forced-recipient mean does not
transfer to the stronger complete controller. Both adapters remain
below the verified feature-head baseline. The data support retaining
the verified component as the stronger measured checkpoint. The two
families have prior project exposure, and their rate presentations
share underlying private conditions. These are bounded next-token
decisions and modeled transmission, with no new final prose.

Both successful fits ran on NVIDIA RTX PRO 6000 Blackwell Server Edition.
The first launch stopped at adapter target matching before optimization.
The live model's module paths differ from the paths in the checkpoint
index. The failed launch is preserved, then the four matches are
recovered using CPU meta construction. The successful runs preserve
the backbone, update eight adapter tensors and replay all restricted
logits exactly after reloading each saved adapter on the same device.
[Failed launch](failed-no-module-match/error.txt) · [Native fit verification](verification.json) · [Direct-credit receipt](credit-evidence/complete.json)

## Verify

Use the project inference environment and run from this directory:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python score_run.py | cmp results.json
python verify.py | cmp verification.json
python credit_score.py | cmp credit-results.json
```
