# Resolution 2686 chair prompt revision

The revised prompt solves the full-receipt word-cap failure in the
original desk order. It reduces the final from 190 to 109 words, but
conflates Switzerland's omitted reference to the International Covenant
on Civil and Political Rights with separate women's rights proposals.
The guard blocks release. Reversing the order brings the same
conflation and exceeds the cap by three words. Pooled raw sources
improve from 21 to 28 released points.

The paired test reuses the original three Qwen3.5-4B notes and the
exact original writer user messages across eight receipt masks, reversed
full receipt, and pooled original sources. Only the writer system
instructions change. The frozen checkpoint, greedy decoding, 288-token
output bound and 175-word final cap are shared. All ten new calls
complete, with 6,017 input tokens, 1,468 output tokens and 25.15 seconds
of measured generation, excluding checkpoint load, on NVIDIA RTX PRO
6000 Blackwell Server Edition. The owner PID is absent after the
completed run. One same-assistant reading grades ten unique opaque
answer packets under the original case rubric. No optimizer updates
or answer edits were made. [Paired protocol](protocol.md) ·
[Native calls](evidence/calls.jsonl) · [Quote-checked scores](scores.json)

| Inputs | Original words | Revised words | Original raw / release | Revised raw / release |
| --- | ---: | ---: | ---: | ---: |
| Public only | 127 | 79 | 14 / 14 | 7 / 0 |
| France | 158 | 72 | 14 / 14 | 7 / 0 |
| Switzerland | 148 | 78 | 21 / 21 | 21 / 21 |
| France and Switzerland | 170 | 80 | 35 / 35 | 14 / 14 |
| UK | 143 | 70 | 0 / 0 | 7 / 7 |
| France and UK | 151 | 83 | 14 / 14 | 7 / 7 |
| Switzerland and UK | 153 | 86 | 28 / 0 | 7 / 0 |
| All three | 190 | 109 | 35 / 0 | 7 / 0 |
| All three reversed | 167 | 178 | 14 / 0 | 21 / 0 |
| Pooled original sources | 161 | 127 | 21 / 21 | 28 / 28 |

All revised records identify the co-sponsors, draft, adopted resolution
and unanimous vote. The revised public-only record says the UK took the
vote and claims agreement about the resolution's meaning. The UAE
presided, and the national explanations preserve distinct reservations.
The revised France-only record assigns ambiguity to the Charter and
changes a topic-specific forum recommendation into a claim about human
rights debates generally. These are source errors capable of nullifying
the downstream value of a correctly delivered note.

## Routing crossover

Keep each adaptive and matched fixed pair of policy tables and openings
constant when changing the writer bank. Then repeat with policies
replanned from the revised bank. Both planners keep the same
calibration and uncertainty structure. Independent branch enumeration
reproduces 72 receipt distributions and scores each distribution against
both writer banks.

| Router calibration | Evaluated writer | Adaptive wins / losses / ties over matched fixed | Mean net difference | Adaptive mean released points |
| --- | --- | --- | ---: | ---: |
| Original | Original | 8 / 0 / 10 | +0.0558 | 22.65 |
| Original | Revised | 3 / 5 / 10 | −0.0040 | 12.51 |
| Revised | Original | 14 / 4 / 0 | +0.1577 | 11.79 |
| Revised | Revised | 12 / 6 / 0 | −0.1233 | 10.57 |

The fixed-opening crossover attributes a drop of 10.14 expected
released points to changing the writer alone under the original
adaptive policy. The replanned adaptive policy delivers the UK card
in 44.5% of modeled receipt mass and delivers all three in 2.85%.
The original policy delivers neither. Even the positive relative
comparison of the replanned router with the original writer has much
lower absolute documentary release than the original setup. Six
matched revised rows fall below informed silence. In the separate
frozen forecast comparison, the learned correction loses to its
neutral counterpart in 17 and ties one, averaging −0.0423 net points.
The data support a synthesis bottleneck on this exposed case, with
simulated routing and no independent reading.
[Crossover protocol](routing-protocol.md) · [Full crossover](crossed.json) ·
[Replanned policies](route-results.json)

The existing 63-point authored assembly shows that the original notes
can fit under the cap. The native revision shows that a shorter output
can still drop or distort the evidence. A claim-preservation check
needs to distinguish the legal instrument from the separately omitted
proposals before another end-to-end comparison can attribute gains to
learned communication. [Assembly control](../README.md#retrospective-assembly-control)

## Reproduce

Run from this directory using the Aurora environment and the
`replay` wrapper in the [parent reproduction instructions](../README.md#reproduce).

```bash
set -o pipefail
cmp ../docket.json docket.json
"$py" writer_revision.py plan | cmp plan.json -
"$py" writer_revision.py verify | cmp verified.json -
"$py" revised_scores.py | cmp scores.json -
replay ../route_tolerance.py --scores "$PWD/scores.json" | cmp route-results.json -
replay cross_writer_routes.py | cmp crossed.json -
```
