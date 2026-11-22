# Resolution 2664 with a fixed factual record and a native comparison

**The model added a useful comparison in one of the two display orders.**
The fixed factual record carried the vote, exemption scope, regime-specific
period, safeguards, and India's account. The model could append a comparison
using the cards it received. Each composition below uses the saved native
output without rewriting it. [Prior full-brief crossover](../drafting-crossover/README.md)

| Received evidence | Standalone /70 | With native append /70 | Authored ceiling /70 |
| --- | ---: | ---: | ---: |
| Public cards only | 30 | 30 | 30 |
| Safeguards only plus public cards | 48 | 48 | 48 |
| India only plus public cards | 40 | 40 | 40 |
| Both, safeguards first | 58 | 58 | 70 |
| Both, India first | 58 | 70 | 70 |

The chair returned exactly `NONE` in all three incomplete conditions. With
India first, the added sentence directly contrasted the delegation's assessment
with the two-year exemption and adopted monitoring. The fixed lines preceding
it name the 1267 Committee, the Monitoring Team, and the specific reporting
request. With the safeguards first, the added sentence described India's
assessment and its reasons. It did not identify what monitoring the Council
had adopted in its comparison. The grader accepted its attribution of the
shortfall to India's judgment and gave zero relation credit. This difference
relies on the rubric's requirement for an explicit comparison. [Native outputs](verified.json) · [Assistant grades](marks.json)

Removing the safeguards card from the 70-point record lowers release by
30 points. Removing India's statement lowers it by 22. The separate
standalone contributions were 18 and 10. The extra 12 points measure the
same relationship in both deletion comparisons and would be double-counted
if summed as two separate bonuses. In the reverse display order the native
writer earns zero joint credit. At illustrative independent 75% delivery and
balanced orders, the native composition releases 54.375 on average, versus
51 for the standalone record and 57.75 for the authored ceiling. Requiring both
cards before calling the chair preserves the native scores in this panel while
skipping all three unproductive partial calls.

This is a five-call frozen Qwen3.5-4B test on one exposed event, run on Aurora's
NVIDIA RTX PRO 6000 Blackwell Server Edition. The standalone record is
assistant-authored and the native writer reads curated paraphrases of the
primary sources. The experiment holds that record fixed to isolate the
native comparison. It establishes one observed useful native addition on
this event, in one order, with a source-preserving architecture. The earlier
full-brief run tested a different writer and information route. Released
scores rely on assistant marks, and no learning or independent evaluation
was performed.

```sh
set -o pipefail
python -B study.py plan | cmp plan.json -
python -B study.py verify | cmp verified.json -
python -B annotate.py | cmp marks.json -
python -B score.py | cmp scores.json -
```

[Locked protocol](protocol.md) · [Scores and counterfactual credits](scores.json) · [Primary-source locators and authored anchors](../README.md)
