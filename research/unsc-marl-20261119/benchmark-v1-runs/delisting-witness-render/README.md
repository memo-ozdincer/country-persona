# Select witnesses separately from the comparison sentence

The locked witness renderer emits no comparison on any of the ten
pairs. On Malta, Qwen3.5-4B selects both full excerpts and exceeds the
27-word witness budget. On A3+, it substitutes straight apostrophes
for curly ones and fails exact matching. The model proposes a
comparison on all six real pairs, including the four crosses.

The compact replay keeps the two complete sources in the final record,
appends the connective selected by the model's type, and stores witness
locations separately. It accepts the two apostrophe styles and maps
back to exact offsets in the original source. This post hoc change
restores both supported links. It also exposes incorrect links on
two real crosses and one fictional reversal.

| Writer on the same 96 settings | Credited links /2 | False links on real crosses /4 | Learned team | Best arrival-only |
| --- | ---: | ---: | ---: | ---: |
| Locked witness renderer | 0 | 0 | 35.987 | 37.242 |
| Compact replay, ungated | 2 | 2 | 38.539 | 39.384 |
| Compact replay, prior source gate | 2 | 0 | 40.565 | 39.457 |

The two compact links retain the context needed for full credit.
Malta's note explains the reporting role and Annex I explicitly keeps
the decision with the committee and excludes a recommendation from
the Focal Point. The A3+ note distinguishes a time-bound preference
from the Council's intention for continuing review. The compact
renderer simply uses the label to connect the two source paragraphs.

The unsupported authority links occur on A3+ and Switzerland's notes
paired with Annex I. The A3+ note gives a timing preference and
Switzerland's note identifies a different institution as a model.
Neither describes the adopted division of roles. On the fictional
review reversal the witness does quote the adopted source accurately,
but the selected connective asserts a contrast in timing when the
text actually requires a single review by a deadline. The previously
archived verifier gives the review claim a negative margin of −2 on
that exact reversal. The compact control result above is ungated.

All ten replies completed on a 12-thread AMD EPYC 9575F 64-Core
Processor worker, using 3,071 input and 559 output tokens. The exact
requests and token IDs replayed. The compact result uses the same
generations, one semantic reader, one exposed docket and the previously
trained policies on simulated receipt settings. The prior admission
gate supplies semantic screening. The cost in the policy table is the
simulator's communication cost. No new training or benchmark release
changes occurred.

[Locked protocol](protocol.md) · [Requests](plan.json) ·
[Worker identity](evidence/launch.json) · [Verified replies](verified.json) ·
[Locked renderer replay](results.json) · [Compact replay](compact-results.json) ·
[Prior source verifier](../delisting-2744/README.md)

Run the following in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B witness.py plan | cmp plan.json -
python -B witness.py verify | cmp verified.json -
python -B witness.py score | cmp results.json -
python -B compact.py --score | cmp compact-results.json -
```
