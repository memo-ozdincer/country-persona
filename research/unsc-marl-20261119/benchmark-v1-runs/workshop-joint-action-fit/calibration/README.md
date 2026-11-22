# Calibrate the chair on incomplete evidence

The disclosure-only training mixture was effective on complete note
pairs, but often committed on notes with insufficient support. Fit a
matched 64-update joint controller with one half learned responder mass,
one quarter full disclosure, and one quarter withholding. Keep the
original reward and inference features fixed.

| Held decision check | Full-disclosure training mixture | Balanced training mixture |
| --- | ---: | ---: |
| Supported correct team decisions | 6/8 | 6/8 |
| Supported decisions with full disclosure fixed | 6/8 | 6/8 |
| Supported decisions with withholding fixed | 0/8 | 8/8 |
| Supported deferrals on uncertified archived overlap notes | 0/4 | 1/4 |
| Correct decisions on certified archived impasses | 4/4 | 4/4 |

Both versions disclosed in all eight unforced held worlds. The balanced
mix teaches deference to explicit withholding, with smaller transfer
to incomplete ordinary notes. In the original simulation the false
endorsement penalty is constant over chair actions in nine synthetic
worlds. This provides a responder signal and zero direct chair gradient
for repairing those particular records. Whether a chair detects a
visible inconsistency calls for a separate test.
[Balanced protocol](protocol.md) · [Branch scores, weights and fit trace](balanced.json)

## Test visibly contradictory endorsements

For every world, add a spoken endorsement after the second delegate's
full mandate. In the matched pairs, changing one package letter turns
an endorsement consistent with that mandate into a contradiction. Keep
both versions in the trace. Allocate 25% of training return to these
chair examples and 75% to balanced joint rollouts. The responder receives
zero direct reward gradient from the new examples. The rollout retains
its original action space and evaluations. This is a dependent fit,
locked after inspecting the balanced run.

| Chair | Supported consistent records /8 | Supported contradictory records /8 | Both variants correct /8 |
| --- | ---: | ---: | ---: |
| Frozen Qwen | 2 | 7 | 2 |
| Balanced joint fit | 4 | 0 | 0 |
| Fit with supplemental pairs | 2 | 7 | 2 |

The supplemental policy matches the frozen chair's labels on all 16 held
paired records. It corrects the balanced controller's overcommitment by
returning to the frozen model's pattern of deference. The tradeoff harms
the team. Its unforced supported correct decisions fall from 6/8 to 2/8.
With full disclosure held fixed, the chair falls from 6/8 to 1/8. Replacing
only the frozen responder with the fitted one changes none of the eight
greedy deployments, locating the measured return change in the chair.

On the archived Syria notes, the supplementary fit improves supported
deferrals on overlap from 1/4 to 3/4 while falling from 4/4 to 0/4 on
certified impasses. These outcomes favor the balanced fit as a checkpoint
for complete evidence and leave abstention under ordinary language
unresolved. Distinguish recognition of a concrete contradiction from
a global shift toward deference when evaluating a later intervention.

The 48 additional language observations were encoded on one NVIDIA
RTX PRO 6000 Blackwell Server Edition. The two CPU fits used 64 updates
each with the Qwen weights frozen. They generate no new final records.
The first GPU launch command stopped in its occupancy print pipeline
before starting Python. The corrected command rechecked the device and
made the recorded feature capture. The chair remains finite-action and
the archived note review remains same-assistant evidence.
[Matched prompts](conflict-roster.json) · [Fit protocol](visible-conflict-protocol.md) · [GPU receipt](conflict-evidence/launch.json) · [Exact results and swaps](conflict.json)

## Verify

Run from this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python conflict_roster.py | cmp conflict-roster.json
python verify.py | cmp verification.json
```
