# Replace reviewed gate labels with a frozen LLM judge

Use all 14 distinct source-and-draft pairs in the Resolution 2504 retained-reply experiment. The judge sees the authorized source, requirements and candidate text, with the generator's prompt and prior review hidden. Its pipe-delimited answer gives an exact witness for each field plus a separate fidelity verdict. The host requires exact candidate substrings, a CLEAN fidelity verdict, completed generation and the original 52-word limit. The same outputs support strict withdrawal-motive and chronology-only scoring. [Locked protocol](protocol.md) · [Raw model output](transcript.jsonl)

| Rubric | Reviewed passes accepted | Reviewed failures accepted | Reviewed failures rejected |
| --- | ---: | ---: | ---: |
| Strict | 3/3 | 6/11 | 5/11 |
| Chronology | 5/5 | 4/9 | 5/9 |

All 14 judge outputs parse. The run uses 5,597 input and 1,126 generated tokens. Some exact witnesses are too weak for the required field. The procedural answer “failing to pass” gives an outcome and omits the requested threshold rationale, but the judge approves the field. It also accepts a draft that assigns the amendment tally to the draft resolution and another that invents the object of Russia's amendment. Under chronology scoring, the retained selector's false priority falls on the first generic procedural reply, and it thereby preempts valid topical replies to question 1 and question 2. [Candidate decisions and literal spans](judgments.json) · [Chosen drafts and gate matrices](replay.json)

Under correlated inventories and the chronology rubric, the ideal-trained policy's oracle-gated net is 55.486. With automatic selection, reviewed net falls to 51.489. Taking approvals at face value gives 55.945, overstating audited net by 4.456. The audited gain over the best no-request team using the same automatic gate falls to −0.499. Under uniform inventories the gain is still +1.024. The correlated branch delivers incomplete cards in 44.1% of simulated episodes. The trained policy forwards none of the three approved candidates with material factual errors because of its source and first-candidate choices. These implications use one exposed docket, same-assistant reference labels, frozen policies and modeled transport. [Audited and apparent policy scores](replay.json)

From the parent directory with the pinned local model and project environment:

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_retention_judge.py score facilitator-retention-judge-evidence
python facilitator_retention_judge_replay.py
```
