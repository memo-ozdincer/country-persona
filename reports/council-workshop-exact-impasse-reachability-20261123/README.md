# Exact impasse reachability under FIFO routing

The [budget audit](../council-workshop-budget-headroom-20261123/README.md)
uses necessary bounds. This search checks the corresponding claim
directly at every post-speech cut in the four registered all-Sol
impasse traces. The caps, delegate declaration rule and queue behavior
come from each archived run.

The search enumerates every subset of requests in the mandatory
floor poll, preserves the existing queue, and lets the resulting
speaker provide a legal missing exclusion or yield. When all exclusions
are public, the next speaker can declare impasse. Other nonterminal
actions that leave exclusions untouched can be replaced by a yield
for reachability purposes. They consume the same budget and leave
the same queue. Both caps are enforced. The search uses the full
fictional mandates offline and assumes cooperative future decisions.
Each final witness replays the exact archived prefix through the
actual meeting engine before executing the chosen continuation.

| Trace | First unreachable post-speech cut | Certified witness from last reachable open cut |
| --- | ---: | --- |
| Gulf, Ghana opening | 6 | 10 speeches, 23 calls |
| Gulf, Norway opening | — | 9 speeches, 22 calls |
| Iraq, France opening | 13 | 15 speeches, 50 calls |
| Iraq, UAE opening | 15 | 16 speeches, 55 calls |

In the UAE-opening Iraq trace, the witness reuses the first 50
calls. France requests the floor on call 52, where it originally
passed. It joins the back of the queue, leaving Brazil next after the
UK supplies the same final exclusion. With France
queued, the moderator skips its second floor poll. Brazil then
declares on call 55. The witness uses the original call cap and
requires no early moderator certification. This was a scripted
continuation, and the registered live run remains unresolved.

[Per-speech search results and replayed witnesses](results.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-exact-impasse-reachability-20261123
python3 -B "$out/search.py" | cmp "$out/results.json" -
```
