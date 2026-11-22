# Automatic factual clearance gave an illusory routing gain

On the exposed Resolution 2422 docket, both sender policies learned to
select passages that the automatic judge rewarded. The peer policy scored
**3.22 and 4.85 points higher** than independent selection at the fitted
availability rate, depending on speaker order. **Both differences were
zero under the archived review.** The automatic guard was the sole change
to terminal scoring. The rubric marks, frozen writer replies, and length
and generation caps came from the same archived action bank.

| First desk at 0.65 passage availability | Automatic score, independent → peer | Reviewed score, independent → peer | Probability of selecting a wrongly released brief, independent → peer |
| --- | ---: | ---: | ---: |
| Peru | 25.42 → 28.64 | 19.06 → 19.06 | 23.1% → 34.2% |
| Joint Russia–Serbia desk | 21.42 → 26.28 | 0.00 → 0.00 | 68.1% → 72.0% |

The automatic peer advantage stayed positive at held availability rates
0.45 and 0.85. Reviewed advantage remained zero. The learned peer policy
attained the exact peer optimum for the automatic reward in both orders at
all three rates. Under review, the independent and peer optima were equal.
Fitting either policy directly on the reviewed reward also reached those
reviewed optima. The learned independent policy missed its automatic
optimum by 0.17 points in the second ordering at 0.65. Relative to the exact
independent optimum, the automatic peer advantage was still 4.69 points.

## What the guard cleared

Across 16 briefs, the guard cleared seven of nine reviewed failures and
three of four uncertain briefs. Caps still blocked five of those ten
briefs. The other five earned newly released scores of 27–39. In three,
the review identified a named voting roster unsupported by the evidence,
which supplied the tally and identified Russia's abstention and Serbia's
nonvoting participation. Two placed Peru's enforcement examples in language
that could read as an operative Council provision. All five got a clear
label under both label mappings. Requiring agreement across mappings
would preserve every mistaken release that affected selection here.
[Full archived guard annotations](../tribunals-source-action-bank/verdicts.json)

For a training objective on this action space, the automated label needs
an evidence-based check before it can authorize credit. In particular,
verify named voting rosters against an explicit roster and bind operational
details to their speaker or instrument. The protected renderer already
demonstrates how to retain those distinctions when the output uses
structured source passages. Its unfitted rubric rule matched the learned
policy on this docket. A new claim for learned communication calls for a
docket with reviewed peer headroom and comparison with an unfitted rule.
[Protected routing comparison](../protected-tribunals-routing/README.md)

## Reproduce

The [protocol](protocol.md) and [input pins](plan.json) fix the ordering,
judge, action bank, and fit. [Raw logits](evidence/labels.jsonl) preserve
32 letter scores with prompt tokens. [Results](results.json) include all
action rewards, exact information bounds, fit traces, and cross-scores.
This is a controlled experiment on one exposed docket. The reference
uses assistant annotations, and the training fits tabular selectors.

Use the project Qwen environment. The score command replays the four
selector fits on CPU using captured logits. The verification command
reconstructs the logged input tokens from the local Qwen tokenizer.

```bash
set -o pipefail
python -B study.py plan | cmp plan.json -
python -B study.py verify | cmp verification.json -
OPENBLAS_NUM_THREADS=1 python -B study.py score | cmp results.json -
```

The [launch receipt](evidence/launch.json) identifies the Aurora GPU and
process. The worker exited normally. The score replay matched byte for byte.
