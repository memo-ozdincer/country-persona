# Cross opening-note deletion with an owner-verified reply

Verified corrections reach the Resolution 2739 chair and improve
specific rubric items. All eight conditions still receive zero released
points under the first review. The unchanged chair supplies unsupported
comparisons even when the opening comparison is removed and the reply
explicitly scopes the available evidence.

## Matched writer outcomes

Keep the original chair prompt and test two independent binary edits
in both desk orders. Delete just the unsupported comparison at the end
of the opening note, or replace the second note with an authored reply
checked against that delegation's source. Compare both edits together
with each alone and with the archived source-check baseline. The
authored replies are evidence controls. The first edits leave the other
opening sentences as generated. [Protocol](protocol.md) · [Locked prompts](plan.json)

| First desk | Neither edit | Delete opening comparison | Replace second note | Both edits |
| --- | ---: | ---: | ---: | ---: |
| Co-sponsors | 14–14 | 14–14 | 14–28 | 21–49 |
| Algeria | 14–14 | 28–28 | 21–21 | 21–21 |

Cells show raw lower and upper bounds out of 70. The combined-edit
interaction on the lower bound is +7 with co-sponsors opening and −14
with Algeria opening. In the first order, the combined edits recover
Algeria's implementation objection, including the sovereignty
qualification. When Algeria opens, both authored-reply conditions
recover the co-sponsors' rationale for timely, accurate information
for Council deliberations. The apparent negative interaction in that
order comes from losing credit for explicit adoption, which the
deletion-alone condition preserved. No final retains the reference
to paragraph 10 of Resolution 2722. [Exact rubric spans](final-marks.json) ·
[Scores and factorial contrasts](results.json)

## Why the guard still fails

- **Co-sponsors open.** The combined edit gives the chair a correct
  account of Algeria's objection to perceived misuse of self-defence
  against sovereign countries. The final describes Algeria as believing
  the underlying framework could legitimize attacks “on its sovereignty”.
  The official explanation raised a general principle about sovereign
  territory. It gave no account of attacks on Algeria.
- **Algeria opens.** The authored reply states that the sponsors'
  explanation establishes no separate position on military authorization.
  The two corresponding finals say they were “explicitly stating no
  position on military authorization”. This changes an evidence gap
  into a claimed utterance. The combined-edit record adds unsupported
  agreement on the cessation demand.

All eight finals end normally and fail the source guard. Four of the
six new finals also exceed the 130-word cap. With the chair fixed, the
released reward is flat across the four note choices in either order.
The exact gradient of that reward is zero for both decisions at any
action probability. At a uniform Bernoulli policy, the raw-score
gradients with respect to the two action logits are (+0.875, +0.875)
with the co-sponsors opening and (+1.75, 0) with Algeria opening.
Raw coverage leaves the new false attributions unpriced.
[Opaque review packets and complete records](verified.json)

The six physical calls use 3,234 input and 1,458 output tokens on
NVIDIA RTX PRO 6000 Blackwell Server Edition. The two baseline replies
are reused without regrading. The run uses one exposed docket and
same-assistant exact-span review. No delegate behavior or model weights
change in this experiment. [Worker receipt](evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from the [parent evaluation](../README.md#reproduce).

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" correction.py plan | cmp plan.json -
"$py" correction.py verify | cmp verified.json -
"$py" score_bank.py | cmp results.json -
```
