# Calibrate the release choice when the writer changes

Two scored probes on Resolution 2744 preserve the compact writer's
useful comparisons and stop the release failures observed when the
desk reuses its old admissions with another writer. The chair uses
the source-only record for candidates with missing or unfavorable
probe scores.

| Writer | Old admissions and frozen routing | Fallback with optimized routing | One probe | Two probes | Best arrival-only after two probes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Compact | 40.286 | 37.242 | 39.372 | **40.438** | 39.372 |
| Topic-guided | 22.727 | 37.242 | 37.242 | 37.242 | 37.242 |
| Generic | 31.544 | 37.242 | 37.242 | 37.242 | 37.242 |

The table includes sending costs and a 0.5-point fee each time
the system uses a comparison. Probe overhead is separate. With
one point per calibration record and a ten-episode horizon,
two probes yield 40.238 on compact and 37.042 on each of the
other writers. Those fees model costs in benchmark points. They
are separate from actual model usage or reviewer time.

The prior source gate nominates two pairs. The frozen compact
policy reaches Malta–authority more often, so the calibration
scores that pair first. It admits it on compact and falls back
on the two other writers. A second probe retains the compact
A3+ comparison. With the first probe alone, content-aware
routing ties best arrival-only. The second creates a 1.065-point
advantage because the reply desk can route either supported note
to its corresponding document. Comparison release rises from
16.96% to 25.43%.

After either writer swap, retaining the frozen forwarding decisions
with the refreshed release rule gets 35.896. Recomputing send
value from the source-only scores reaches 37.242. The stale rules
failed the guard on 25.08% of topic-guided and 8.13% of generic
episodes. Refreshed decisions had zero guard failures across all
three writer banks. A software check changes the unprobed output
and confirms that the one-probe decisions and scores are unchanged.

This uses archived outputs and prior same-assistant grades for the
exact prompts. The gate learns two per-pair admission decisions
from scalar feedback. The routing update is direct optimization
using the estimated table. Scores are deterministic in this replay.
The result applies to a known writer change with scored candidate
records. Wording changes, stochastic output, live calibration costs
and unseen docket transfer require separate evidence. No new model
calls or changes to the closed benchmark were made.

[Locked protocol](protocol.md) · [Probe order and input hashes](plan.json) ·
[Calibration traces, costs and all held settings](results.json)

```bash
set -o pipefail
python3 -B calibration.py --plan | cmp plan.json -
python3 -B calibration.py | cmp results.json -
```
