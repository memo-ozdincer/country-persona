# One targeted question recovers a missing qualification

Start from the six manually audited supported atoms in the interactive Resolution 2719 notes. The original automated verifier admitted a seventh atom based on partial evidence. Use the audited six as the starting record for all arms. Under the frozen rubric, obtaining the French qualification about both UN and EU contribution levels can add seven points, while recovering the missing US reading can add five. This determines the requested field. [Audited starting point](../facilitator-2719-evidence-admission/results.json) · [Prospective comparison](protocol.md)

| Follow-up | New qualified evidence | Audited material / 70 | Input / generated tokens |
| --- | --- | ---: | ---: |
| None | — | 58 | 0 / 0 |
| Generic request for one new fact | Repeats the concern about the funding gap | 58 | 234 / 30 |
| Targeted question | Recovers willingness to discuss both UN and EU contribution levels | 65 | 236 / 26 |
| Targeted question with supporting sentence withheld | Repeats the earlier note | 58 | 210 / 43 |

The live targeted reply copies the approved French sentence exactly. The paired generic reply copies the other source sentence, repeating a fact already in the draft. The withheld reply fails to report absence and instead copies the earlier note, which names only the EU. Source membership blocks that reply. The supplement preserves six preapproved facts in all arms and includes the new clause only with verified evidence. The two positive arms use one call, the same model and the same token cap. Input counts differ by two tokens. [Raw replies and token trace](transcript.jsonl) · [Exact source checks and composed results](results.json)

This is a live causal comparison of one observable difference in the follow-up prompt on an exposed event. The request comes from a rubric-based marginal score and uses a same-assistant audited starting draft. The generation endpoint uses an authored source-card atom and fixed prose. There is no new trained policy or estimate of general deliberation quality. The withheld control shows that earlier-note access also creates a provenance hazard worth carrying into held-out interaction tests. [Source card and five final criteria](../facilitator-resolution-2719-evidence/packet.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_2719_followup.py score facilitator-2719-followup-evidence
```
