# Where the budget made completion impossible

This audit replays the [eight registered all-Sol traces](../council-workshop-all-sol-matrix-20261123/README.md)
and examines the state immediately after each speech. It records the
first cut where a necessary condition for finishing fails. Each bound
is optimistic about future choices, so a passing cut leaves
reachability open. The calculations use the finite case answer key
offline and require zero new model calls.

For agreement, the bound counts missing signatures if the current
draft is feasible. Otherwise it counts a proposal and all signatures.
For impasse it counts every missing exclusion and a declaration.
Each remaining speech needs a call, the next floor poll covers every
seat outside the existing queue, and subsequent speeches need at least
one new poll. If one seat alone holds a missing exclusion, everyone
already ahead of that seat in the queue has priority. The audit allows
that holder to make its remaining exclusions on consecutive speeches
and budgets one further speech for the declaration.

| Unresolved trace | First cut proved impossible by this audit | Binding constraint |
| --- | --- | --- |
| Gulf, Ghana opening | After speech 6, call 15 | Norway had two exclusions left and was behind two queued seats. The declaration could occur no earlier than speech 11 with a cap of 10. |
| Iraq, France opening | After speech 13, call 46 | France still held the only `closed` exclusion and was behind four queued seats. The declaration could occur no earlier than speech 19 with a cap of 16. |
| Iraq, UAE opening | After speech 15, call 53 | All exclusions were public. Two required floor polls and one declaration needed three calls when two remained. |

The bounds remained compatible with success at every cut of the five
completed traces. They also distinguish two different repair points.
The Gulf and France-opening Iraq runs needed a sole holder to disclose
earlier. In UAE-opening Iraq, the evidence was already complete and
only the closing procedure exhausted the available calls.

The Gulf scripted suffix checks reachability just before the detected
failure. It reuses the first **14** requests and replies exactly. On
speech six Norway rules out `briefing`. Ghana and Norway supply the
remaining exclusions, and Ghana declares on speech ten, call 23. The
suffix is a scripted witness within the original caps. The standard
trace remains unresolved in the registered score.

[Per-speech bounds and scripted suffix](results.json) ·
[France-opening reachability witness](../council-workshop-iraq-pilot-20261123/README.md) ·
[UAE-opening call-cap replay](../council-workshop-moderator-certificate-20261123/README.md)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-budget-headroom-20261123
python3 -B "$out/audit.py" | cmp "$out/results.json" -
```
