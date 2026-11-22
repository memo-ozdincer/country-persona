# Hold source delivery fixed and retest the Council writer

Use the four editorial tasks on Resolution 2730 with each of the two
one-card receipts. The chair receives the same documentary text as
in the archived runs. Keep the same checkpoint and 136-token final
cap. Change the writing instructions to specify the three-part
record, full vote tally, task-specific attribution or gap, and an exact
operative verb. Eight new CPU generations are compared with eight
previously reviewed matching inputs. The original baseline uses the
first archived record in the declared policy order for each matching
receipt. One receipt has two distinct original outputs, both preserved
and scored in the sensitivity entry. The instructions were chosen
after examining the original outputs.

| Evidence delivered | Prompt | Editorial criterion | Integrity guard | Mean points | Strict |
| --- | --- | ---: | ---: | ---: | ---: |
| Relevant card | Original | 2/4 | 0/4 | 35.0/70 | 0/4 |
| Relevant card | Revised | 4/4 | 3/4 | 59.5/70 | 0/4 |
| Other card | Original | 0/4 | 0/4 | 24.5/70 | 0/4 |
| Other card | Revised | 0/4 | 3/4 | 38.5/70 | 0/4 |

All revised outputs give the complete tally and abstaining actor.
All eight use “calls for” in the investigations passage. The source
card uses that wording about respect for international humanitarian
law and uses “urges” about investigations. Six state a defensible
limit on the Council action, and one still says States are mandated
to investigate. Two hit the output cap. None uses all required
bracketed citations. Only one of the four wrong-card responses states the
requested gap. Another credits Russia with omitting its own proposals.
Scores are exact-span same-assistant annotations under the existing
rubric. Literal selection of the operative verb and response completion
are recorded separately. There were zero optimizer updates.

## Check the reward before fitting the routing policy

With the original writer, sending the other Russia card on the
omissions task earns more partial credit from a better-rendered
vote. The best task-aware selector and best blind selector both score
38.5/70. Under the revised writer every relevant receipt earns more
than its paired irrelevant receipt, with a mean difference of 21 points. The best blind
policy reaches 52.5/70, and targeted delivery reaches the task-aware
ceiling of 59.5/70. Strict reward is still zero across the eight views.

Replaying the original one-card selections through the revised
writer gives 54.25/70 for the generated peer question, 49/70 for
independent selection, 52.5/70 for always sending card A, and
59.5/70 for the verbatim question. These are exact receipt replays
from one finite table of actual generated records. The matched
input views exclude the two-card solo and direct-all arms. Verbatim
querying reaches the ceiling, so this fixture can diagnose a bad
reward and test the writer but provides no endpoint headroom over
verbatim querying at the same delivery allowance.

[Per-view scores, citations and ceilings](results.json) ·
[Exact review spans](grades.json) ·
[Archived source packet and original run](../facilitator-requested-evidence/README.md)

```bash
python facilitator_authority_writer.py verify facilitator-authority-writer-evidence
python facilitator_authority_writer_score.py facilitator-authority-writer-evidence --grades facilitator-authority-writer-evidence/grades.json
```
