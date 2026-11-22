# Carry live grade reports into a workshop memo

Use two capability branches selected by the frozen enumeration. The learned opening and exact chair planner choose the disclosure slots. Frozen Qwen3.5-4B transcribes the authorized opening reports and the requested grade, while the chair recomputes its request using only admitted openings. Each report is checked against the sender and authorized grade. The private cards are fictional. [Locked protocol](protocol.md) · [Frozen branch selection](scenarios.json)

For each branch, cross the final reply's delivery with visibility of the formal certificate. The direct writer gets the public rule and admitted receipts. The certificate writer also gets the compatible-world count and the permissible decision computed from those same receipts. In the erased arm we keep the opening, question, attempted-message budget and final call ceiling, then remove the follow-up from the final input. The Mali branch requires the worse-off preference even when total grades tie. The briefing branch becomes an impasse after the second report. Both erased views are unresolved. [Runnable branch selection and policy](../warrant_live.py)

A final record earns 25 points for the permitted decision, 15 for its exact receipt list, 20 for the evidentiary explanation and 10 for fictional workshop scope. Complete release requires all four, an exact JSON envelope, at most 90 memo words and no material error. A fenced JSON object can receive diagnostic material credit and still fails the strict format. The model writes fresh replies and memos. The cited historical agendas motivate the synthetic workshop labels, while the memo contains only workshop authority and evidence.

## Results

The complete-card writer emits zero of four authorized opening reports. All four use the wrong package or grade and the boundary check rejects them. With no accepted opening, the chair asks a different question in the Mali branch and receives one authorized reply. Neither live branch reaches the planned certificate. The three strictly releasable baseline memos all record absence of evidence and come from direct empty-ledger views. Two are the same prompt. [Raw outputs](final-records.json) · [Exact-span review and baseline results](results.json)

The correction gives the writer only the designated delegate, package and grade. It uses placeholders for the line format and keeps the received question outside the writer. All four openings and both follow-up replies pass the same gate. Both planned follow-ups reach the chair, and the correct decisions are B and IMPASSE. Removing either reply leaves that branch unresolved. The underlying learned routing choices, physical link outcomes and final instructions are held fixed. The correction changes what the writer can read and its format instruction together. [Targeted correction protocol](authorized-only/protocol.md) · [Exact reply and final traces](authorized-only/results.json)

| Final writer after correction | Warranted labels | Exact receipt lists | Fully releasable records |
| --- | ---: | ---: | ---: |
| Direct language model | 2/4 | 4/4 | 0/4 |
| Language model with certificate | 4/4 | 4/4 | 1/4 |
| Deterministic renderer | 4/4 | 4/4 | 4/4 |

The direct model leaves both delivered decisions unresolved. The certificate fixes their labels. The Mali memo nevertheless says that only B is viable. A is also feasible, and B wins because its worse-off grade is two versus A's one, with both totaling four. Several erased-view memos also confuse having no common best option with having no feasible option. The deterministic renderer from the same actual receipts explicitly distinguishes those cases and fits the 90-word limit. The language-model prose grades use same-assistant exact-span review. The renderer's explanations follow the programmed rule and reproduce the admitted reports. [Reviewed outputs](authorized-only/review.json) · [Compiled records](authorized-only/compiled.json)

This tests the integration of the archived local policy, exact requester, authorized generated reports and final records on two capability branches. The final comparison estimates neither policy advantage over public planning nor general natural-language deliberation quality. The transmitted grades are workshop evidence and confer no official authority.

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
python warrant_live.py verify warrant-live-evidence
python warrant_live_score.py score warrant-live-evidence
python warrant_live_authorized.py verify warrant-live-evidence/authorized-only
python warrant_live_score.py score warrant-live-evidence/authorized-only --authorized-only
python warrant_live_compile.py warrant-live-evidence/authorized-only
```
