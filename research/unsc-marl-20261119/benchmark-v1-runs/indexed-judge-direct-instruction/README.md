# Remove contradictory quote instructions from the indexed judge

The revised prompt still yields **zero usable verdicts out of four**
on the targeted slice. The two final verdicts copy prose into
citation fields and also put an answer ID where a source block ID
belongs. One process verdict uses valid passage IDs in parts of
its reply but lists ideas without turn citations. The other leaves
required turn citations empty. The source binder and published
validator reject these replies.

| Selected anchor | Failure after rewriting the instructions |
| --- | --- |
| Full Myanmar final | Copies prose and uses an answer ID as a source block |
| False Syria authorization | Raw verdict flags the guard correctly. Citation formatting fails. |
| No peer exposure | Passages resolve. The verdict lists ideas with empty turn citations. |
| Retained correction | Empty quote fields in idea mentions fail address binding. |

The same selected packets failed in the original 25-packet indexed
trial. The new prompts preserve the identical indexed evidence,
criteria and output budgets. They replace the old quote-copying
instructions and examples with passage IDs. The model's continued
format errors on the two finals show that the earlier prompt
conflict explains only part of the failure.

All four replies completed on NVIDIA RTX PRO 6000 Blackwell Server
Edition, with 8,068 input and 5,085 output tokens. Both final outputs
are semantically inspectable as diagnostics. Neither enters the
benchmark result. This is a targeted same-checkpoint test on exposed
anchors and does not estimate the usability of other judges or
unseen cases. The full indexed experiment and frozen v1.7 remain
available separately.

[Protocol](protocol.md) · [Locked requests](plan.json) ·
[Captured replies](evidence/tokens.jsonl) · [Token receipt](verified.json) ·
[Calibration results](results.json) · [Full indexed run](../indexed-judge-calibration/README.md)

```bash
set -o pipefail
python -B clean.py plan | cmp plan.json -
python -B clean.py verify | cmp verified.json -
```

Run `python -B clean.py replay --output NEW_DIRECTORY` to replay
the original validator against the retained responses.
