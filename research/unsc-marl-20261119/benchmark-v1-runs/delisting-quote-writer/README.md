# Ask the frozen chair to quote the operative source language

The quote instruction earned neither relationship bonus. Qwen3.5-4B
returned `NONE` for the supported Malta–Annex I pair. On the A3+
pair it called continuous review an adopted provision, where the
Council source says it expressed an intention to review continuously.
The unchanged prompt made the same two substantive errors.

| Writer on the same 96 routing settings | Credited links /2 | Learned team | Best arrival-only |
| --- | ---: | ---: | ---: |
| Generic control, rerun on CPU | 0 | 31.578 | 37.242 |
| Exact-quote instruction | 0 | 31.578 | 37.242 |
| Preserved standalone facts | 0 | 35.987 | 37.242 |
| Two credited links over preserved facts | 2 | 40.565 | 39.457 |

The A3+ answer put “continuous review” in quotes as part of its
description of the Council provision. That consecutive phrase occurs
in the delegate note. The supplied Council text uses “expressed its
intention to review the Focal Point’s mandate and work continuously.”
The other two quoted phrases fail a literal substring check because
punctuation appears inside the quotation marks. Removing that punctuation
can recover text matches but leaves the error in legal force.
All four crossed pairs received `NONE` in both arms.

The reward replay isolates each relationship over the same factual base.
With only Malta credited, the learned team reaches 39.039 and the
arrival-only control reaches 39.457. With only A3+ credited, they
reach 37.513 and 38.349 respectively. Together the two credits create
a 1.108-point advantage. This is a sensitivity on authored rewards,
with the original trained routing policies fixed.

The 12 calls ran on one AMD EPYC 9575F 64-Core Processor worker with
12 threads, BF16 and greedy decoding. All six inputs were matched
between arms except for the added system instruction. The CPU control
reproduces five of six archived GPU replies exactly. The changed A3+
wording retains the same scoring status. The quote prompt used 1,751
input and 44 output tokens across six calls. The control used 1,355
input and 39 output tokens. The outputs use one semantic reader on
an exposed docket and the replay uses simulated receipts. No model
weights or benchmark release files changed.

[Protocol](protocol.md) · [Locked requests](plan.json) ·
[Worker identity](evidence/launch.json) · [Verified responses](verified.json) ·
[Quote results and literal checks](results.json) · [CPU control](control-results.json) ·
[Relationship credit sensitivity](credit.json)

Run these checks in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B quote_writer.py plan | cmp plan.json -
python -B quote_writer.py verify | cmp verified.json -
python -B quote_writer.py score | cmp results.json -
python -B control.py | cmp control-results.json -
python -B credit.py | cmp credit.json -
```
