# Scope the final writer and measure the reward from verified notes

A scoped chair prompt still releases zero points on all eight
Resolution 2739 note pairs. A reviewed source-bound composer releases
42/70 with the archived notes and 49/70 with an owner-verified reply in
both desk orders. The seven-point gain comes from the verified
delegation explanation.

## Generative chair comparison

Reuse the eight pairs from the [correction bank](../README.md). Append
one instruction to the chair's system prompt. It prioritizes the public
record, limits each attributed position to its own note, and calls for
affirmative evidence from both sides before recording agreement.
The user message, note contents, model, and 280-token generation
budget are identical within each pair. The factual guard and
130-word limit remain the same. [Locked prompts](plan.json) · [Protocol](protocol.md)

| First desk | Neither edit | Delete opening comparison | Replace second note | Both edits |
| --- | ---: | ---: | ---: | ---: |
| Co-sponsors | 7 | 21 | 7 | 14 |
| Algeria | 21 | 21 | 28 | 28 |

The table shows the raw lower bounds out of 70 under the new chair
prompt. Four improve by seven points and four lose seven points
relative to their original-chair counterparts. All new records finish.
Two exceed the word limit, versus four for the original chair.
Every record fails the guard. The new chair still confuses Algeria's
support for receiving reports with support for the extension or the
cessation demand. With the co-sponsors opening and only the reply
replaced, the final preserves the deadline qualification in the last
line while elsewhere claiming agreement on the reporting extension.
With Algeria opening and both notes edited, the final says the
sponsors explicitly stated they had no military-authorization
position. The note only described a gap in what their source established.
[Blind final packets](verified.json) · [Exact-span grades](final-marks.json) ·
[Matched scores and reward gradients](results.json)

## Source-bound comparator

After reading the generative results, assemble the same receipt pairs
with a 42-point authored public block and only previously reviewed,
exact excerpts from each correctly attributed note. The public block
always preserves the adoption, draft, sponsors, tally, operative
paragraph, reporting date and authority limit. Hand review supplies
the case-specific admissible excerpts. Swapping the role labels
rejects all excerpts, and withholding note text rejects its excerpt.
The composer emits no cross-delegation comparison from these inputs.
No note pair contains the complete verified reporting rationale on
both sides. The comparator makes no new model calls.

| First desk | Neither edit | Delete opening comparison | Replace second note | Both edits |
| --- | ---: | ---: | ---: | ---: |
| Co-sponsors | 42 | 42 | 49 | 49 |
| Algeria | 42 | 42 | 49 | 49 |

The table shows released points. All records pass the guard and use
57–79 words. The authored reply adds Algeria's full abstention reason
with co-sponsors first, or the co-sponsors' complete reporting
rationale with Algeria first. Deleting the unreliable comparison
has zero effect because the composer admits only the reviewed
excerpts. At uniform Bernoulli action probabilities, the released
reward gradients are zero for deletion and +1.75 for reply replacement,
in points per unit of action logit. Both generative chairs yield zero
for both gradients. This is a measured reward difference with manual
admission and an authored public lead. A fixed rule to send the
verified reply already reaches the available ceiling here.
[Exact composed records, admissions and scores](source-bound.json)

The eight frozen Qwen3.5-4B forward-generation calls consume 5,280
input tokens and 1,291 output tokens on NVIDIA RTX PRO 6000 Blackwell
Server Edition. The project worker exits normally. The outcomes
use one exposed docket and same-assistant review. Deployable
semantic admission and cross-family improvement remain unmeasured.
[Worker receipt](evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from the [first evaluation](../../README.md#reproduce).

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" chair_scope.py plan | cmp plan.json -
"$py" chair_scope.py verify | cmp verified.json -
"$py" score_scope.py | cmp results.json -
"$py" source_bound.py | cmp source-bound.json -
```
