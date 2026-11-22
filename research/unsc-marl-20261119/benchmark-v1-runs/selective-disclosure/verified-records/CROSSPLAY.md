# Calibrate an unfamiliar opener from retrospective chair receipts

Cross the frozen recipient with two authored partner conventions.
One normally reports its highest grade to the chair. The other
normally reports its lowest. In the silent condition neither
copies the chair report to the peer. In the shared-peer condition,
both use the same paid disclosure on first cards with maximum
grade three. They differ in their other chair reports.

The recipient's own cards and peer messages have precisely the
same distribution under both partners, including erasures and
silence. They still induce different evidence at the chair.
Posterior adaptation from local histories cannot distinguish them.
The retrospective record adds the authenticated first report that
reached the chair on a previous turn. The recipient can use past
records to infer its partner while the current verifier still sees
only current authenticated grades.

The experiment checks the two partner policies by exact integration
on the four reserved outer-space grids and the canonical Mali and
Myanmar-linked grids. Across grids and partner conditions, it
renders and verifies 697 receipt-view instances. Some views repeat
across conditions. The separate original decision evaluator checks
the resulting policy scores.
[Cross-play protocol](crossplay-protocol.md) · [Receipt and policy replay](crossplay.json)

## Value of past reports

The table averages both openers and all six grids. These returns
include the original peer-message fees. The four prior records in
this comparison have no separate access fee.

| Condition | Frozen fixed recipient | Frozen rank fit | Equal-mixture planner | Planner with four archived receipts | Known-partner ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Always silent | 0.602652 | 0.590116 | 0.602652 | 0.614652 | 0.614705 |
| Shared peer reports | 0.575947 | 0.568812 | 0.578839 | 0.586018 | 0.586071 |

Four archived receipts recover more than 99% of the gap between
the equal-mixture and known-partner planners in both conditions.
Local observations stay at exactly 50% identification at all
tested history lengths. In the shared-peer condition on grid 217,
the two scripted partners use identical opening choices, so even
the full retrospective reports supply no distinguishing evidence
and identification stays at 50%.

## Charge for accessing the archive

A dependent exact stopping calculation offers up to four reads.
After each read it compares the next-turn value of stopping with
the costed expected reward from another read. Read costs below
are modeled at 0.003 normalized points each. Every choice uses
the same future turn, legal messages and verifier.

| Available receipt fields | Silent net | Silent reads | Shared-peer net | Shared-peer reads |
| --- | ---: | ---: | ---: | ---: |
| Delivery presence | 0.602652 | 0.000 | 0.578839 | 0.000 |
| Package only | 0.608760 | 0.816 | 0.583247 | 0.446 |
| Numeric grade only | 0.612951 | 0.518 | 0.584873 | 0.333 |
| Full authenticated report | 0.613394 | 0.419 | 0.585316 | 0.234 |

Receipt presence supplies no partner information. Numeric grade
alone retains most of the useful signal for these high-grade and
low-grade partners. The full report is more informative and
requires fewer expected reads. The average includes grids where
the planner skips the archive entirely. Paying for all four
full reads gives 0.602652 and 0.574018, respectively. The adaptive
policy improves over the no-read planner at all three evaluated
prices in both conditions.

The candidate partner rules and stationary grade distribution are
supplied. A mismatch outside this pair could invalidate the
posterior. Records are mechanically verified in simulated
workshops. No new language calls, recipient weight updates or
independent prose judgments enter this test.
[Reading-cost protocol](receipt-access-protocol.md) · [Exact access decisions and returns](receipt-access.json) ·
[Preparation corrections](crossplay-preparation.md)

## Reproduce

Use the existing project Python environment.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python crossplay.py | cmp crossplay.json -
python receipt_access.py | cmp receipt-access.json -
```
