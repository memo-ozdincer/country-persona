# Test separate factual checks for procedure, authority, and attribution

Splitting the factual guard made it worse on the 33 reviewed
records. It cleared all 12 historical briefs, including the six
marked failed and one marked uncertain in the earlier reading.
Every historical brief received a clear average decision in all
three categories.

| Guard | Anchor matches | Anchor false clears | Historical matches | Historical false clears |
| --- | ---: | ---: | ---: | ---: |
| Single question, two label orders | 17/21 | 1 | 6/12 | 5 |
| Three scoped questions, two orders each | 16/21 | 3 | 5/12 | 7 |

The false Syria authorization remains a false clear. On each
of procedure, authority, and attribution, changing the label
assignment switches the prediction from failed to clear. The
average logit favors clear for all three. Requiring all six
predictions to clear eliminates false clearance on the anchors
but blocks 16 of 17 valid anchors. It still clears two of seven
previously blocked or uncertain historical briefs. [Rule ablations](ablation.json)

The historical release comparison stays at **−4 points** after
the scoped guard replaces the single-question model guard.
The previous assistant reading was **−12 points**. The scoped
guard's two additional false clearances concern briefs already
blocked by a word or token cap, so the released scores do not
change. This isolates a case where another release condition
hides a change in the judge's reliability.

The 198 first-token evaluations used 188,988 input tokens with
frozen Qwen3.5-4B on NVIDIA RTX PRO 6000 Blackwell Server Edition.
The study keeps the source packets, anchor labels and historical
verdicts fixed and changes only the model's guard questions.
Each guard is constrained to three labels. There are no generated
citations or new human ratings in this comparison. The historical
marks are one earlier assistant reading of exposed cases.
The benchmark remains closed.

[Protocol](protocol.md) · [Locked inputs](plan.json) ·
[Individual decisions and replay](results.json) · [Verified traces](verified.json)

```bash
set -o pipefail
python -B scoped.py plan | cmp plan.json -
python -B scoped.py verify | cmp verified.json -
python -B scoped.py score | cmp results.json -
python -B ablation.py | cmp ablation.json -
```
