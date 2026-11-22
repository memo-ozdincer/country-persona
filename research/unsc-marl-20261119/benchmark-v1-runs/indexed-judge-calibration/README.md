# Calibrate a judge that cites numbered passages

The full indexed run produced **zero usable verdicts out of 25**.
Every response contained a value that the citation binder could
not resolve. The new instructions were appended to the published
prompt, which still asked for exact quotations. The model often
followed the earlier instruction and copied prose into quote fields.
In the first Syria verdict it also put a passage ID into a field
reserved for the original block ID.

| Judge interface | Usable final verdicts | Usable process verdicts | Raw final label matches |
| --- | ---: | ---: | ---: |
| Published verbatim quotes | 3/21 | 0/4 | 111/123 |
| Appended passage IDs | 0/21 | 0/4 | 111/123 |

Both modes parse after removing an outer JSON fence when present.
The indexed run gets four of eight raw process labels, matching the
previous envelope-only diagnostic. Eleven of its 12 final label
mismatches are identical to the earlier mistakes. Its raw guard
does flag the false Syria authorization, but the verdict itself
remains unusable. Raw agreement is an error diagnostic separate
from accepted ratings.

The adapter maps only declared sentence IDs and same-text ranges
to exact offsets. Software checks confirm it rejects unknown IDs
and cross-source ranges. It leaves model labels and reasons
unchanged. The original validator receives rebound verdicts and
rejects incomplete calibration. The closed package is unchanged.

Frozen Qwen3.5-4B on NVIDIA RTX PRO 6000 Blackwell Server Edition
ran all 25 captured requests, with 50,353 input and 30,049 output
tokens. This test uses exposed calibration anchors. Its failed
instruction combination is measured separately from the targeted
follow-up that removes the conflicting instructions.
[Dependent four-anchor test](../indexed-judge-direct-instruction/protocol.md)

[Protocol](protocol.md) · [Verified traces](verified.json) ·
[Full calibration results](results.json) · [Raw label diagnostics](raw-labels.json)

```bash
set -o pipefail
python -B indexed.py plan | cmp plan.json -
python -B indexed.py verify | cmp verified.json -
python -B labels.py | cmp raw-labels.json -
```

Run `python -B indexed.py replay --output NEW_DIRECTORY` to reproduce
the calibration result from the stored replies.
