# Check a peer's attribution against the receiving desk's own source

An explicit source-check instruction fails to correct either incorrect
opening on Resolution 2739. Both peer-informed notes repeat the unsupported
comparison. Both chairs carry it into the final. Every final earns zero
released points under the same provisional exact-span review.

## Matched intervention

For both desk orders, reuse the opening note word for word. Replace only
the second desk's system instruction. In both arms it asks for the
delegation's own position, reason and scope, and tells the desk to correct
overbroad attributions if it sees one. The two arms differ in whether the
second desk sees the opening. Collect four second notes and four finals
with frozen Qwen3.5-4B, the original budgets and unchanged chair instructions.
The archived arms provide the generic-instruction counterfactuals.
[Protocol and primary contrast](protocol.md) · [Locked inputs](plan.json)

| First desk | Original independent raw /70 | Original peer raw /70 | Source-check independent raw /70 | Source-check peer raw /70 |
| --- | ---: | ---: | ---: | ---: |
| Co-sponsors | 28 | 14 | 14 | 14 |
| Algeria | 28 | 14 | 14 | 14 |

The source-check independent result in co-sponsors-first has an upper
bound of 28 because the adopted resolution is mentioned parenthetically
without an explicit disposition. Both source-check peer arms tie their
original raw scores. The peer-minus-independent lower-bound gap closes
because independent records lose credit for the disposition. All four
new finals are complete and within the 130-word cap.
[Marks by opaque final packet](final-marks.json) · [Scores and deltas](results.json)

## What reaches the final

- **Co-sponsors open.** Algeria's peer-aware reply repeats agreement on
  the extension and disagreement over the cessation demand. The chair
  upgrades the inferred disagreement to an explicit assertion that
  Algeria did not support that demand. The second desk never states
  Algeria's documented view that continued reporting kept the Council
  informed. The independent response reports the abstention rationale
  but also omits the reporting distinction.
- **Algeria opens.** The sponsors' peer-aware reply repeats the inferred
  split over military authorization. It characterizes the sponsors as
  seeking only information gathering. The final carries that formulation
  forward and adds a claim of shared support for the cessation demand.
  The independent sponsors' note identifies that its own source does not
  give Algeria's rationale. That qualification fails to constrain the
  final, which repeats the opening note's unsupported inference.

Both peer notes terminate normally at 50 and 61 words. The 61-word note
exceeds the 55-word instruction. Both independent second notes reach the
100-token cap. Completion alone did not make either peer note faithful.
The peer paths add 89 and 109 logical input tokens to the matched
independent paths, with the same call count and token caps.
[Working notes, final packets and tokens](verified.json) ·
[Exact notes-to-final evidence](flow-marks.json)

The eight physical calls use 4,598 input and 1,284 output tokens on
NVIDIA RTX PRO 6000 Blackwell Server Edition. The project worker exits
normally. The case, archived generic outputs and scores are exposed.
The review is from the same assistant. This experiment changes a prompt
and tests whether a receiver spontaneously checks provenance. It leaves
the effectiveness of trained correction and independent judge agreement
unmeasured. [Worker receipt](evidence/launch.json)

## Reproduce

Run with the same Aurora Python environment as the
[parent evaluation](../README.md#reproduce).

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" source_check.py plan | cmp plan.json -
"$py" source_check.py verify | cmp verified.json -
"$py" score_check.py | cmp results.json -
```
