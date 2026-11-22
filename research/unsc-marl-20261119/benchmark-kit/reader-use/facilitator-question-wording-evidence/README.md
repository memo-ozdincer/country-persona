# Separate topical questions from stronger local authoring

Freeze the Resolution 2719 source cards, the Qwen3.5-4B checkpoint, the reply rule and the 92-token cap. Generate two new matched questions per card and two generic instructions shared across sources. The generic instructions can be supplied to each independent writer without inter-agent communication. Each output finishes under 52 words. The 12 calls use 2,033 input tokens and 728 generated tokens. Eight pass the existing strict coverage and authority guard. An initial exact-span review had an extra comma in one witness. Correcting its punctuation allowed the score replay. The candidate and rubric are unchanged. [Protocol](protocol.md) · [Candidate questions](questions.json) · [Blind exact-span review and outputs](admission.json)

| Source | New generic passes | New matched-question passes |
| --- | ---: | ---: |
| Procedure | 2/2 | 2/2 |
| United States | 0/2 | 2/2 |
| France | 1/2 | 1/2 |

The US result extends the archived contrast from one question to three observed targeted phrasings. All three preserve the US interpretation of the original draft, rationale for an explicit ceiling and action on the amendment. Neither new generic instruction nor the original silence reply preserves the original interpretation under the same strict rubric. France's missing predictability qualification can be recovered by either type of prompt. One variant of each succeeds.

## Frozen policy replays

Replace the original silence row with either generic alternative and optionally change all three matched diagonal replies to the corresponding new wording. Keep the old off-topic cells, all policy parameters and the loss assumptions unchanged. For each resulting matrix compare the ideal-trained policy against the best no-request policy given that matrix with hindsight.

| Reply matrix | Uniform gain | Correlated gain |
| --- | ---: | ---: |
| Archived replay | +2.399 | +2.929 |
| First generic row only | −0.339 | +1.676 |
| First generic row and first set of matched questions | +2.496 | +2.563 |
| Second generic row only | +2.399 | +2.929 |
| Second generic row and second set of matched questions | +2.399 | +2.929 |

The first generic row improves the no-request uniform score from 51.338 to 54.293, enough to beat the learned policy while it uses the original questions. Applying the first set of matched questions also improves the learned policy's use of the France reply. The second paired matrix has the same pass pattern as the archived matrix. Thus the US result survives rephrasing while the size and direction of the team comparison still depend on the full prompt interface. With source assignments, physical loss and record assembly simulated, these results apply to these authored prompt variants and one exposed docket. The judge is the same assistant as earlier reviews. No fitting occurs here. [Five exact simulation replays](replay.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_question_wording.py blind facilitator-question-wording-evidence
python facilitator_question_wording.py score facilitator-question-wording-evidence
python facilitator_question_wording_replay.py
```
