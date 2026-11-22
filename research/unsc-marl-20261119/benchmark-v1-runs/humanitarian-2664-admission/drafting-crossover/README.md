# Resolution 2664 drafting crossover

**Peer reading produced no release gain in either order.** All six Qwen3.5-4B
briefs connected the adopted monitoring to India's concerns. All six also made a
material source error. The chair could infer the comparison from independent
notes, and peer access did not reliably preserve the underlying legal language.

| First desk | Arm | Raw /70 | Released /70 | Final words | Input tokens across three calls |
| --- | --- | ---: | ---: | ---: | ---: |
| Adopted safeguards | Independent | 22 | 0 | 127 | 719 |
| Adopted safeguards | Peer-informed | 36 | 0 | 166 | 814 |
| Adopted safeguards | Pooled solo | 22 | 0 | 130 | 947 |
| India | Independent | 36 | 0 | 125 | 719 |
| India | Peer-informed | 22 | 0 | 128 | 772 |
| India | Pooled solo | 22 | 0 | 117 | 988 |

Four briefs described the Council as exempting providers **from providing**
humanitarian resources. Paragraph 1 exempts qualifying transactions from
asset-freeze restrictions. The two remaining briefs turned a request for
reasonable efforts, including due diligence, into a stronger obligation.
The 166-word safeguards-first peer brief also hit the generation cap and
exceeded the 150-word task limit. No run met the two-year provision criterion
in full or stated the zero count against. [Adopted text](https://digitallibrary.un.org/record/3997259) · [Meeting record](https://digitallibrary.un.org/record/3997357/files/S_PV.9214-EN.pdf)

The India-first peer safeguards note combined both sides of the comparison
before the chair wrote. It also introduced an unsupported deadline for
addressing India's objection before expiry. The chair repeated that claim.
The preceding India-only note had called for addressing the gaps without
asserting a deadline. The safeguards-first peer note inherited an overstated
due-diligence obligation from the independent safeguards note, and the chair
strengthened it into an obligation to minimize benefits. Peer access added
53–95 input tokens over independent drafting within the same call and output
cap budgets. The raw score difference reversed with order.

This is one previously exposed docket with assistant review against the
[locked six-item rubric](../case.json). The [judge packets](blind.json) omit
condition and transcript. Human review by a separate annotator and LLM judge
reliability remain unmeasured. Collection used frozen greedy Qwen3.5-4B on
Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition. The 14 physical calls
cover 18 logical turns through shared local notes. Reproduction checks saved
request and output tokens, while the substantive grades are assistant marks.
There were zero optimizer updates.

The result isolates a chair-writing failure that would contaminate terminal
rewards to the desks. The authored 70-point record shows that both the
exemption and the minority objection can fit the task cap. On the same evidence,
a source-preserving public lead is the direct candidate to test against these
native chairs. That comparison would hold the model accountable for the
relationship it adds and measure whether it can keep the adopted-text scope
and reporting modality intact. [Calibration anchors](../README.md)

```sh
set -o pipefail
python -B study.py plan | cmp plan.json -
python -B study.py verify | cmp verified.json -
python -B score.py --blind | cmp blind.json -
python -B annotate.py | cmp marks.json -
python -B score.py | cmp scores.json -
```

[Locked design](protocol.md) · [Six briefs and note chains](evidence/briefs.json) · [Marks and exact spans](marks.json) · [Scores](scores.json)
