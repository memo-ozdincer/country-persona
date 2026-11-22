# Learn passage selection with a source-preserving tribunal chair

The protected chair releases all **16** exact passage-and-order
combinations for **38–52 points**, compared with one released
record under free-form synthesis. The learned second desk uses
the first note when it changes which passage is worth sending.
The gain is small and matches an unfitted rule derived from the
same published rubric.

| Private card availability | First desk | Learned independent /70 | Learned peer /70 | Peer gain |
| --- | --- | ---: | ---: | ---: |
| 45%, held | Peru | 46.791 | 46.791 | 0 |
| 45%, held | Russia and Serbia | 46.791 | 46.870 | 0.079 |
| 85%, held | Peru | 50.434 | 50.434 | 0 |
| 85%, held | Russia and Serbia | 50.434 | 50.529 | 0.094 |
| 65%, training | Peru | 48.515 | 48.515 | 0 |
| 65%, training | Russia and Serbia | 48.515 | 48.627 | 0.111 |

The chair assembles the published vote and appointment passages,
the first sentence of the limits card, and exactly one excerpt
from each desk. Each brief is 123–136 words and passes the original
release contract under the documented source bindings. The omitted
public sentence concerns the separate question of early release
for persons convicted by the ICTR. The renderer adds no claims to
the excerpts. The tribunal's published contrast criterion can earn
credit when the delivered pair preserves both Peru's appeal for
unity and Russia's staffing rationale. [Complete records and verdicts](bank.json)

When both Peru passages are available, the learned peer policy sends
the unity appeal after Russia's staffing note. Unity plus the contrast
earns six points. It sends Peru's five-point state-cooperation passage
after the other notes. The strongest independent policy favors that
five-point passage regardless of the first selection. The positive
effect occurs only when Peru follows the combined Russia and Serbia
desk. Averaging both orders halves the gain.

Both policies start from the same zero logits and receive the same
shared terminal score. They complete 256 exact expected-reward
updates over independently retained private slates, with each slate
conditioned to contain at least one available passage. Only the
second peer desk receives the exact earlier choice. The analytic
gradient replays and is checked by finite differences. Evaluation
uses greedy legal choices and two held card-availability rates.

The supported comparison is between information conditions. Both
learned policies attain the exact information-specific optimum.
An unfitted method that knows the published scoring requirements
attains those same values. The reward here is mechanically visible
from the input evidence. The fit learns the selection rule on one
exposed family with an authored source-bound scoring map, and leaves
the effectiveness of generative drafting and novel-event transfer
open. The closed benchmark remains intact.

[Protocol](protocol.md) · [Complete released records](bank.json) ·
[Locked fit](plan.json) · [Policy weights and exact evaluation](results.json) ·
[Prior free-form matrix](../tribunals-source-action-bank/README.md)

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B render.py | cmp bank.json -
python -B learn.py --plan | cmp plan.json -
python -B learn.py | cmp results.json -
```
