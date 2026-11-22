# Source-local purpose quotes for the Resolution 2739 chair

**Both desks found the relevant evidence. Passing those quotes to the chair
added zero points in either order.** The co-sponsor desk extracted the
purpose of providing accurate, timely information for deliberations about
the attacks. The Algeria desk extracted the purpose of keeping the Council
informed. The desk shown only the adopted action abstained. The two admitted
quotes were exact spans of their respective source cards. [Quotes and chair outputs](verified.json)

| Delivered cards | Direct chair /70 | With quotes /70 | Require two admitted quotes /70 |
| --- | ---: | ---: | ---: |
| Both statements, co-sponsors first | 56 | 56 | 56 |
| Both statements, Algeria first | 56 | 56 | 56 |
| Public action and Algeria, action first | 49 | 0 | 49 |
| Public action and Algeria, action second | 49 | 49 | 49 |

The direct chair returned `NONE` for both complete pairs. With the quotes
and Algeria first, the chair named each purpose accurately but left the
shared reason implicit. On one crossed view it treated Algeria's purpose
as shared even though no other delegation's statement was present. The
source guard blocked release. Requiring an admitted quote from each card
before calling the chair would skip both crossed calls and restore the safe
49-point fallback. This checks that both inputs carry source text. It does
not establish that the two quoted purposes are equivalent.

The two full-evidence quote-assisted paths each use 659 logical input tokens
versus 291 for the direct writer, including both local desk calls. The
extractions are reused across orders. The crossed paths also pay two desk
calls, including the public-action abstention. Overall 11 physical calls use
3,104 input and 186 output tokens. The prompts and token traces replay exactly.
Collection used frozen Qwen3.5-4B on Aurora's NVIDIA RTX PRO 6000 Blackwell
Server Edition. [Locked protocol](protocol.md) · [Costs and release scores](scores.json)

The comparison isolates access to short quotes while the full cards and final
prompt stay fixed. The extra calls give no benefit on this exposed docket
under the existing criterion. Assistant marks assess the exact relation and
guard. The partial scores imported from the previous study are fixed-fact
references and were not rerun here. No model or MARL policy weights were
updated. The observed gap is semantic composition after faithful extraction.
The complete-pair terminal reward remains purely additive in both arms.

```sh
set -o pipefail
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B study_driver.py plan | cmp plan.json -
"$python" -B study_driver.py verify | cmp verified.json -
"$python" -B annotate.py | cmp marks.json -
"$python" -B readout.py | cmp scores.json -
```

[Scoring marks](marks.json) · [Original rubric and evidence](../docket.json)
