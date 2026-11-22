# Execute the third-delivery policy through live English messages

The chair uses the frozen action-value policy, a fixed script or
the exact independent opening and delivery table. The learned
and scripted chair use the existing public opening plan, which
matches the first two sends of the independent control. The two
opening deliveries take the same archived reviewed notes in
each arm. The branch fixes the inventories and opening loss
before any language generation.

An English question carries the chosen topic to the responding
desk. The decoder receives the question and a public menu of
topics whose numeric labels change by episode. A separate
payload call receives only the note authorized by the decoder
and that arm's local delivery table. Note transmission requires
the model to return the full authorized sentence, including any
citation already attached. A failed guard discards that
delivery and keeps its charge. The final selects the reviewed
mask-specific record, with proof that every admitted transmitted
note appears unchanged in it.

This design isolates live communication from new factual
extraction and prose composition. It uses preapproved evidence
notes and a locked record compiler. The two model calls per
arm have the same maximum lengths. The implementation batches
identical prompts once and counts them in each arm's logical
budget. Guarded points and the 21-point completion bonus compare
docket records. The net subtracts transport fees. The experiment
does not estimate a population success rate from four selected
branches. [Protocol and exact lineup](protocol.md) ·
[Seven-weight fit](../facilitator-third-paired-evidence/action-values.json)

UNIFIL uses UNBench author-test event 2497 and adopted UNSC-Bench
row 241. Myanmar uses the 21 December 2022 UNBench author-test
vote and official Council transcript. The pinned UNSC-Bench
scan has no Myanmar match.
[UNIFIL release join](../../../crossbench/unifil-reserve.json) ·
[Myanmar release join](../../../crossbench/myanmar/references.json)

## Initial live result

Frozen Qwen3.5-4B decodes eight of ten unique prompts, including
all four silences. It transmits all six requested evidence notes
exactly and returns the expected `NONE` once. The decoder uses
1,088 input tokens and 20 output tokens. The payload stage uses
558 input tokens and 167 output tokens. Across policy arms, the
17 physical generations serve 24 logical calls.

| Branch | Learned | Fixed requests | Independent |
| --- | ---: | ---: | ---: |
| UNIFIL complementary evidence | 63 | 63 | 49 |
| UNIFIL complete record | 70 | 70 | 70 |
| Myanmar role note available | 56 | 49 | 56 |
| Myanmar requested role note missing | 49 | 63 | 49 |

All twelve receipt masks match the typed predictions. The model
misses both versions of the procedural-role request by selecting
the sponsorship topic in one branch and silence in the other.
In the first branch the learned desk sends the only useful card
on every possible decoded topic. In the second, the wrong decode
and the true but unavailable request both lead the learned policy
to repeat the India national-position card. Receipt equality thus
masks two communication errors. A valid request is needed to
choose among genuinely available alternatives.
[Live decoder and payload outputs](transcript.jsonl) · [Scored records](results.json)

```bash
python facilitator_live_delivery.py verify facilitator-live-delivery-evidence
python facilitator_live_delivery_score.py facilitator-live-delivery-evidence
```

## Retest the procedural-role request

Specify India explicitly and name the sequence of Council procedure,
national speech and return to the presidency. Keep the original
numbered menus. The two new generations both return digit 2.
That digit is correct in one menu and selects the national
explanation in the other. The paired procedural decode improves
from 0/2 to 1/2, and sensitivity to the menu remains.

On a separately selected stress branch, the desk has all three
Myanmar cards and receives the same public query and menu as the
repaired case. Its private inventory changes the response action.
The original silent decode delivers India’s national note again,
leaving the final at 49. The repaired decode delivers the
procedural note and raises it to 56. This stress replay reuses
the actual decoded digits and already transmitted evidence.
The wording and the stress branch were chosen after inspecting
the two original failures. The total is 19 actual generations,
and the repair adds no new reply or final writer call.
[Retest trace](role-repair/transcript.jsonl) · [Stress replay](role-repair/results.json)

```bash
python facilitator_live_delivery_role_repair.py score facilitator-live-delivery-evidence/role-repair
```
