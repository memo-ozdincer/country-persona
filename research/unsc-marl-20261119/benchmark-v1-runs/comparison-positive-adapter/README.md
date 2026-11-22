# Train the writer only on supported comparisons

Keeping the 24-update budget, replacing abstentions with additional
positive exposures made the adapter write on all six 2744 pairs.
**Neither matched pair earns relationship credit.** The source gate
holds the learned team's utility at 31.578, the same as frozen Qwen.
Without the gate, the new crossed-pair errors lower utility to 29.552.

| Writer on the 96 held routing settings | Comparisons credited /2 | Learned utility, admitted | Learned utility, ungated | Best arrival-only, admitted |
| --- | ---: | ---: | ---: | ---: |
| Matched frozen writer | 0 | 31.578 | 31.578 | 37.242 |
| Mixed positive and NONE fit | 0 | 35.987 | 35.987 | 37.242 |
| Positive-only fit | 0 | 31.578 | 29.552 | 37.242 |
| Typed reference | 2 | 40.565 | — | 39.457 |

On Malta's matched pair, the writer states that the Focal Point
provides a report and the committee decides. It then adds a supposed
Malta recommendation element absent from the delivered statement.
Its 42-word draft exceeds the 40-word cap and falls back to the
preserved sources. The A3+ draft repeats the contrast
between speaker and text, but says the Council adopted continuous
review where the text expresses an intention. It receives the same
uncertain legal-force judgment as the frozen version. The ungated
Swiss responses assign an unsupported substantive interpretation to
the Ombudsperson comparison. The actual gate discards those crossed
comparisons before release.

There are six distinct positive training examples from 2721 and 2664,
each used four times. The mixed fit used the same positives twice
alongside six abstentions. The runs match updates, seed, learning rate,
LoRA projections and decoding. The positive-only fit sees 752
supervised tokens including closing tokens, versus 400 for mixed.
All held prompts are identical to those of the prior fit and excluded
from optimization. All six newly generated frozen outputs match
the earlier matched controls. The delivery-value sender and reply
policies are fixed.

This comparison separates willingness to generate from faithful
realization on the same exposed holdout. It uses one semantic
reader and simulated receipt conditions. The adaptation objective
supervises the language writer. The fixed source gate checks whether
the two sources support a comparison, without rechecking the
semantics of the resulting draft.

The 24 updates and twelve generations ran on NVIDIA RTX PRO 6000
Blackwell Server Edition. The backbone's parameter versions remain
unchanged. The on-disk adapter reproduces the held probe logits
exactly. No benchmark release files changed.

[Locked split](plan.json) · [Worker identity](evidence/launch.json) ·
[Stored adapter and token evidence](evidence/complete.json) ·
[Direct token audit](audit-reuse.json) · [Verified replies](verified.json) ·
[Semantic marks](marks.json) · [Policy replay](results.json)

The direct audit matches all training token arrays against the previously
audited mixed-fit pack and decodes every held response from its token IDs.
Run the following in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B positive_fit.py plan | cmp plan.json -
python -B audit_reuse.py --verified | cmp verified.json -
python -B positive_fit.py score | cmp results.json -
python -B audit_reuse.py | cmp audit-reuse.json -
```
