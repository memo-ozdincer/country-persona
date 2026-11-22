# Audit role-owned evidence admission on Resolution 2719

Freeze the nine note generations from the three-arm live comparison. Qwen3.5-4B selects exact supporting spans for eight facts per note set. The host checks that every span occurs in the authorized role's note and that the output has exactly one row per claim. The case renderer builds a supplement from selected facts and appends the fixed Council anchor. The semantic audit uses the same assistant as the prior benchmark review and is separate from the model's decisions. [Protocol](protocol.md) · [Frozen notes and original final scores](../facilitator-resolution-2719-evidence/results.json)

| Note set | Host-admitted witnesses | Semantically supported | Audited material / 70 | Audited release |
| --- | ---: | ---: | ---: | --- |
| Interactive | 7 | 6 | 58 | Fail |
| Independent | 7 | 4 | 48 | Fail |
| Solo | 4 | 2 | 42 | Fail |
| Fully supported control | 8 | 8 | 70 | Pass |
| Contradicted control | 1 | 0 | 42 | Fail |
| Wrong-owner control | 0 | 0 | 42 | Public anchor only |

Of the 18 live exact-span admissions, 12 support their claims, four fail semantic support and two are uncertain. The incomplete French willingness statement names only the EU, but the model accepts it for the claim requiring both the UN and EU. The independent US note contains the reason for the cap, but the selected excerpt merely reports submission and advocacy. The solo tally witness omits votes against, and its two-word France fragment omits the voting category. In the contradicted control, the model copies an exact sentence naming France as author of the US amendment. Structural membership passes that error. The wrong-owner control returns owner numbers in place of claim IDs, so the parser drops all eight rows and emits only the verified public anchor. This tests the format fallback. [Raw outputs](final-records.json) · [Host decisions](admission.json) · [Exact-span audit](results.json)

Dropping each role's previously admitted atoms yields an eight-view replay of audited support. The interactive note set reaches 58 with all three roles, versus 48 with the procedural role alone. The model's verifier withholds some correct information before rendering and admits several unsupported witnesses. These replay scores vary with the actual notes. They describe fixed witness erasure, with no new verifier call at each mask. The interactive supplement has six supported atoms after audit, with the missed French contribution-level qualification offering seven material points. This is the starting state for the paired follow-up experiment. [Role-erasure scores](results.json)

The initial score command caught a manual mark accidentally entered for one unbound witness. The mark was removed because the host had rejected that span; no raw output was changed. The dependent follow-up's first invocation stopped at the empty report, before model inference. It was launched after successful reproduction of the score. [Follow-up protocol](../facilitator-2719-followup-evidence/protocol.md)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
evidence=facilitator-2719-evidence-admission
python facilitator_2719_admission.py verify "$evidence"
python facilitator_2719_admission_score.py "$evidence"
```
