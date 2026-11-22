# Pass a verified comparison topic to the 2744 writer

A topic question induced prose on the Malta pair that the generic
writer skipped. The new prose still omitted who decides a petition.
Its possessive wording, “Malta's Focal Point,” also made the actor's
identity ambiguous. The A3+ response described continuous review as
adopted and gave the working group a mandate to execute it. The
adopted text instead expresses an intention and assigns the group
review of the Focal Point's reports. Neither generated comparison
earns the 18-point relationship bonus under the original rubric.

| Writer on the same 96 settings | Learned team | Best arrival-only |
| --- | ---: | ---: |
| Earlier whole-record Qwen prose | 6.210 | 16.001 |
| Fixed standalone facts only | 35.987 | 37.242 |
| Generic Qwen comparison, with source admission | 31.578 | 37.242 |
| Topic-guided Qwen comparison, without admission | 22.761 | 37.022 |
| Topic-guided Qwen comparison, with source admission | 22.761 | 37.168 |
| Typed relation reference | 40.565 | 39.457 |

The topic comes from the existing delegate-side verifier, which selected
procedure for Malta and review timing for the A3+. A new question
asks about the decision-maker or the legal force and timing. It supplies
no candidate comparison. Four prompts changed by exactly this added
field. The two Swiss prompts were identical to the generic arm. All
twelve generations across both arms used greedy decoding on the
same checkpoint and NVIDIA RTX PRO 6000 Blackwell Server Edition GPU.
The earlier whole-record baseline used AMD EPYC 9575F 64-Core Processor
hardware and a different writing assignment.

The ungated stress replies put the proper topic question on crossed
receipts as well. On Malta's review-only receipt, the draft invents
a conflict between the working group and sanctions committees by
equating review of reports with deciding individual cases. On the
A3+ authority-only receipt, it writes explanatory prose instead of
the requested exact abstention and ambiguously denies that the
adopted text has review terms. The fixed role admission suppresses
these two crossed additions. It cannot verify the generated meaning
of sentences on the admitted pairs. The gated content-aware oracle's
small strict advantage comes from avoiding blocked records.

A permissive sensitivity treats Malta's sentence as supported without
a relationship bonus and gives A3+ full relationship credit. Then the
admitted learned team scores 37.513. The arrival-only and content-aware
ceilings are both 38.349. That favorable reading still leaves the
second relationship missing.

The six focused calls used 1,557 input and 137 output tokens. The
operational gate would run two of the six comparison calls on this
receipt bank. The score continues to deduct only the simulator's
existing communication cost. This is one exposed case and one semantic
reader. The source gate and replayed routing policy were frozen. No
language-model weights or benchmark release files changed.

[Protocol](protocol.md) · [Locked prompts](plan.json) ·
[Exact responses](verified.json) · [Semantic marks](marks.json) ·
[Policy replay](results.json) · [Permissive sensitivity](sensitivity.json) ·
[Generic comparison](../delisting-comparison-writer/README.md)

With the existing Aurora Qwen environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B focused.py plan | cmp plan.json -
python -B focused.py verify | cmp verified.json -
python -B focused.py score | cmp results.json -
python -B lenient.py | cmp sensitivity.json -
```
