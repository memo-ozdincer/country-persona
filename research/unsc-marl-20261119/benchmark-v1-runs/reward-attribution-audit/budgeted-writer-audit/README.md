# How many writer audits do the senders need?

A release gate trained on other dockets recovered **zero of three native
improvements** in 74 paired compositions across five dockets. The improvements
were two split-writer drafts on Resolution 2553 and the India-first append
on Resolution 2664. The rerun includes the measured 2664 append and keeps the
same length and lexical features as the earlier draft-aware gate.

The usable policy in this panel was to audit individual drafts and retain a
draft only when its paired audit showed a gain. A favorable audit was a weak
basis for admitting other drafts from the same writer. On the 2553 split writer,
one uniform audit improved release by 0.069 points on average when applied
to the directly inspected draft. Applying a favorable report to the entire
writer instead lost 2.333 points on average. The larger four-audit budget still
lost 0.604 points under that writer-level rule.

| Writer with an observed improvement | Audits | Direct, uniform gain /70 | Direct, ranked gain /70 | Oracle gain /70 |
| --- | ---: | ---: | ---: | ---: |
| 2553 split | 1 | 0.069 | 0.000 | 0.833 |
| 2553 split | 2 | 0.139 | 0.000 | 0.833 |
| 2553 split | 4 | 0.278 | 0.333 | 0.833 |
| 2664 append | 1 | 1.200 | 0.000 | 2.400 |
| 2664 append | 2 | 2.400 | 2.400 | 2.400 |

At two audits on 2664, both non-identical candidates have been graded. The
other three receipt contexts return identical text and require no audit. On
2553, the ranked fourth audit retained the 4-point improvement and missed
the 6-point one. Direct audit gains are conditional on the archived grades
accurately measuring improvement. Reported results average release across
all receipt contexts, including the untouched safe fallbacks.

## Consequence for the send decisions

Reuse the same 12 delivery and order settings and cost function from the
2664 sender fit. Before an exact audit, the router anticipates the fixed
fallback. After the audit, it uses the scored effect of each admitted
append to recompute both send decisions.

| 2664 feedback | Mean released /70 | Mean cost-adjusted utility |
| --- | ---: | ---: |
| No fresh audit | 30.000 | 30.00000 |
| One audit, cross-docket ranking | 30.000 | 30.00000 |
| One uniform audit | 37.414 | 30.58075 |
| Both order variants audited | 44.828 | 31.16150 |

The cross-docket ranking spent its first audit on the safe tie, so it
created no new incentive to send. The uniform result is the average across
the two possible audit selections. Auditing both restores the previous
oracle utility on this grid because all eight terminal mask and order
combinations can then be reconstructed from the matched grades. Here the
constructed send cost is held fixed. Audit effort is counted separately
and is excluded from the utility score.

The archive is same-assistant graded and all target dockets are exposed.
Strata vary by architecture, and append variants can share the same
source pair. The fit tests transfer across absent docket families, then
few-shot feedback over finitely many archival candidates. It supplies no
evidence of generalization from one writer's favorable output to new
live drafts. The two-order 2664 routing replay assumes known deployment
probabilities and an already available fallback.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B audit.py --plan | cmp plan.json -
python -B audit.py | cmp results.json -
python -B routing.py | cmp routing.json -
```

[Protocol](protocol.md) · [Per-writer audit results](results.json) · [Routing replay](routing.json)
