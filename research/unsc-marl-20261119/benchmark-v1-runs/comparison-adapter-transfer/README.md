# Train a relation writer on other dockets and test it on 2744

A 24-update Qwen3.5-4B adapter returned **NONE on all six 2744
pairs**. The matched frozen model declined five pairs and generated
one A3+ comparison with ambiguous legal force. The adapter removes
that admission error. It leaves both legitimate comparisons unwritten.

| 2744 writer, fixed learned routing | Receipt relationships earning credit | Learned utility | Best arrival-only |
| --- | ---: | ---: | ---: |
| Matched frozen Qwen | 0/2 | 31.578 | 37.242 |
| 24-update adapter | 0/2 | 35.987 | 37.242 |
| Typed relationship reference | 2/2 | 40.565 | 39.457 |

The adapted team's apparent utility gain equals the result of displaying
the verified facts alone. Changing the text writer does not close the
role-aware routing gap under the authored relationship score. The two
valid pairs remain unsupported by generated comparison prose.

The training pack contains six positive examples and six exact NONE
targets on 2721 and 2664, including paraphrases of the two training
dockets. No 2744 prompt or output enters the optimizer. Loss is
computed only on completion tokens and the closing token, with one
example per update and two passes. The mean observed pre-update loss
for the NONE examples moves from 0.317 to 0.194 across passes,
and the mean for positive examples moves from 2.467 to 2.415.
These are training traces in changing minibatch order.
The fit updates eight LoRA tensors in the query and value projections
of full-attention layers 27 and 31. All frozen parameter versions
stay unchanged. The first held next-token probe reloads exactly
from the saved adapter and every adapted generation follows that reload.
The newly captured frozen texts match the six previous texts exactly.

This is one small writing fit, evaluated on an exposed docket excluded
from the fit, with the existing manual semantic marks and fixed
routing policies. The original attempt cost and simulated delivery
remain in the utility. The adapter receives supervision on source
realization. Neither desk policy was restarted or updated.

All computation ran on NVIDIA RTX PRO 6000 Blackwell Server Edition.
The 459,832-byte adapter stays in the run directory on project storage.
No benchmark release files changed.

[Locked split and inputs](plan.json) · [Held outputs and adapter receipt](verified.json) ·
[Target-token and exposure audit](audit-fit.json) · [Semantic and policy scores](results.json) ·
[Worker identity](evidence/launch.json)

With the existing Aurora Qwen environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B train_writer.py plan | cmp plan.json -
python -B train_writer.py verify | cmp verified.json -
python -B audit_fit.py | cmp audit-fit.json -
python -B score_transfer.py | cmp results.json -
```
