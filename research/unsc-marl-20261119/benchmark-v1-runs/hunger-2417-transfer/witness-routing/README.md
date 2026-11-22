# Compile the two Resolution 2417 comparisons from checked evidence

Selecting evidence instead of drafting prose recovered the US reporting
comparison in both source orders. It still left no peer advantage on
its own. Filling in omitted witnesses from the exact reviewed sanctions
packets recovered the second relationship. The learned peer policy then
matched the **40.565** optimum after **1,024 simulated scores**, versus
**39.457** for best arrival-only. A fixed rule that used the same
register reached the same score in every held setting.

| Chair method | Exact arrival-only | Exact peer | Peer benefit |
| --- | ---: | ---: | ---: |
| Earlier revised free-prose writer with reviewed fallback, canonical order | 39.457 | 39.457 | 0 |
| Strict witness selection with source-only fallback, either order | 38.349 | 38.349 | 0 |
| Complete witnesses on exact registered packets, either order | 39.457 | 40.565 | **1.108** |
| Unfitted registry-only rule, either order | 39.457 | 40.565 | **1.108** |

Means cover 96 held delivery, cost and prior settings. The repaired
peer fit beats exact arrival-only in 80 settings at 1,024 scores. At
256 scores the peer and arrival-only fits still tie at 39.457. The fit
uses one realized terminal outcome per simulated episode. It reads no
alternate outcomes. It learns passage values from the canonical table
and transfers to the reversed-source-order table, which has identical
scores after repair.

## Where the selector helped and failed

Qwen selected all three reporting witnesses in both historical orders
and one source-preserving paraphrase. That selection distinguishes the
US preference for more frequent country reporting from the Council's
continuation of its existing reporting and its separate request for
swift alerts. The sanctions selection consistently included one span
from each source and omitted the other two. The exact register supplied
the drafters' role and the adopted clause's obstruction scope when both
source panels matched. The completion rule requires partial evidence
from both sources, the correct registered relationship, and no duplicate
or out-of-range witnesses. An unsupported proposal cannot insert text.

The raw model proposed valid-looking links on five crossed historical
packets and three fictional reversals. None released. The register
protects the final record in this experiment and explains the recovery.
The score gives no incremental value to running a native selector on a
fully registered packet. When the model lacks a reusable match, this
implementation keeps the sourced standalone record. The model's false
links, even with structurally valid outputs, leave novel semantic
approval unvalidated.

The adaptive witness-completion rule came after inspection of the strict
outputs. All released comparison wording was already in the parent
case. The model inference outputs and training simulator are
separate. The 18 frozen Qwen3.5-4B calls consumed 5,073 input and 319
output tokens on an NVIDIA RTX PRO 6000 Blackwell Server Edition.
The worker exited normally. The routing fits use NumPy on the 12-cell
archive and make no further model calls or language-model updates.
This is one exposed docket with author-reviewed cards and synthetic
reversals. The two real paraphrases are registered in advance and
measure phrasing stability within that register.

[Source packets](cards.json) · [Strict protocol](protocol.md) ·
[Raw outputs](verification.json) · [Strict replay](results.json) ·
[Repaired records, learned policies and controls](repair-results.json) · [Audit](audit.json)

## Reproduce

Run in the Aurora Qwen environment from this directory.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B select_witness.py plan | cmp plan.json -
python -B select_witness.py verify | cmp verification.json -
python -B replay.py | cmp results.json -
python -B repair_replay.py | cmp repair-results.json -
python -B audit.py | cmp audit.json -
```

The audit replays 576 strict and reference optimal-policy checks,
384 repaired score matches, 2,048 simulated training scores, and 42
altered-source or malformed-witness checks. The preliminary repair
script collided with the release module named `replay`. A path-based
load resolved it before fitting.
