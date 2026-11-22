# Can the final draft tell us whether to release it?

A gate using draft length, lexical retention and novelty, number changes, and
literal prefix preservation kept neither improvement in the held-docket replay.
It also admitted one harmful rewrite. The literal record remains the release
default supported by this panel.

| Held resolution | Drafts | Fallback /70 | Always native /70 | Draft-aware /70 | Oracle /70 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2553 | 36 | 32.33 | 7.19 | 32.33 | 32.61 |
| 2721 | 9 | 43.33 | 27.33 | 43.33 | 43.33 |
| 2686 | 8 | 41.13 | 37.63 | 40.25 | 41.13 |
| 2475 | 16 | 42.00 | 31.50 | 42.00 | 42.00 |

The two improved drafts scored 35 versus 31 and 42 versus 36. Both came from
the split writer on Resolution 2553. That leaves 0/33 improved training
drafts when holding out 2553 and 0/57 when holding out only its split writer.
When the two other 2553 writers were held out separately, the gate chose
the fallback on all 24 contexts. All 24 native alternatives reduced released
points. The gate admitted one tied draft on the held split writer.

On Resolution 2686, the gate admitted a 28-point rewrite of a 35-point
fallback. The fallback-length model admitted only a tie. On Resolution 2475,
both admitted drafts were exact copies of their fallback. The apparent
admission rate there measures no change in the released record.

The 69 alternatives reuse receipt contexts and existing assistant-scored
records. Absolute scores use docket-specific criteria and caps. These averages
weight receipt contexts equally within each writer. The earlier routing replay
applied delivery probabilities and charged for using native generation, so its
reported net scores answer a different question. Here both drafts already exist
when the selector acts. This panel tests a release rule and leaves communication
and the benchmark release fixed.

A gate calibrated for future dockets needs verified improvements from multiple
event families under more than one writer. Assembling that evidence would
require paired outputs with identical source access, scored on release criteria
fixed before drafting. The existing archive cannot provide that cross-writer
training and test contrast for genuine improvements.

Reproduce with Python 3.10 or later and NumPy.

```sh
set -o pipefail
OPENBLAS_NUM_THREADS=1 python -B admission.py --plan | cmp plan.json -
OPENBLAS_NUM_THREADS=1 python -B admission.py | cmp results.json -
```

[Protocol](protocol.md) · [Per-context results](results.json)
