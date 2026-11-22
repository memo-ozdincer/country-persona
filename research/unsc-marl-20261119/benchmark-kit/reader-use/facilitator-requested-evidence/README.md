# Request evidence from the other desk

This development probe uses the Council's 24 May 2024 meeting on
humanitarian personnel. The record distinguishes Council adoption,
Russia's abstention and explanation, and Switzerland's account of
the Secretary-General's follow-up. The packet contains normalized
summaries of the official vote, operative paragraph 13, and selected
statements in the meeting record. The editorial questions and
division of source access are authored for the probe.
[Official meeting record](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9634&t=pdf) ·
[Resolution text](https://digitallibrary.un.org/record/4049572/files/S_RES_2730_%282024%29-EN.pdf)

Each private deck contains two passages. Two editorial tasks use
exactly the same deck and public record, with a different relevant
passage for each task. The first desk sees the editorial question.
The second desk sees the two candidate passages and can send one
whole card. In the peer arm, the first desk drafts and sends a
question. In independent drafting, one selection per delegation is
made before receiving the editorial question and reused across its
two tasks. The independent arm uses the same opening call in its
compute accounting. The final writer always sees the editorial
question and public record.

Verbatim query forwards the editor's original question directly,
uses the same selector and sends one card. Direct-one always sends
card A and makes only the final call. Direct-all forwards both
cards, with a higher transfer allowance and only the final call.
The three-pass solo arm sees both cards at the selection and writing
stages and uses its question and selection as working notes. All six
arms use the same final output cap. Peer and independent use the
same planned call budget. Actual tokens and evidence delivered
are counted separately.

A blind selector that sees only the deck can deliver the right
card on at most half the four tasks, since the task is balanced
within each deck and the selector's inputs are identical. A
query-aware policy can in principle deliver it on all four. These
are ceilings for source delivery. The final writer can still
lose material that was delivered. Blind and verbatim controls
help identify whether a gain comes from having the query, asking
a better question, or using the answer in the final.

The pinned UNBench author-test vote matches all 15 official votes
for event 2531. The pinned UNSC-Bench adopted and vetoed tables
contain no matching draft or meeting. The historical sources
carry the speaker claims and the scope of Council action.
[Packet](packet.json) · [Executable archive audit](../facilitator_requested_evidence_provenance.py) ·
[Provenance](provenance.json) · [Frozen rating instructions](rubric.md)

## Frozen Qwen3.5-4B result

| Arm | Relevant card available | Editorial requirement met | Mean final points | Strict briefs |
| --- | ---: | ---: | ---: | ---: |
| Generated peer question | 3/4 | 1/4 | 26.25/70 | 0/4 |
| Independent selection | 2/4 | 2/4 | 38.50/70 | 0/4 |
| Verbatim editorial question | 4/4 | 2/4 | 31.50/70 | 0/4 |
| Three-pass solo | 4/4 | 3/4 | 47.25/70 | 0/4 |
| Direct forwarding, one card | 2/4 | 1/4 | 29.75/70 | 0/4 |
| Direct forwarding, both cards | 4/4 | 1/4 | 35.00/70 | 0/4 |

The real question gives the source desk a useful signal. The
generated question sends the wrong card on the six-month
recommendations task after reframing the question as a choice
between adoption and a later report. All four generated questions
hit their token cap. All 14 card selectors end and return one
permitted letter. No peer final preserves an editorial requirement
that its paired independent final missed. In the recurring-reporting
contrast, some writers omit who must report and others omit the
recipient even when the correct source reaches them.

All 24 final responses explicitly attribute the abstention to
Russia. All 24 also turn the Council's urging of States to
investigate into a mandate. The final-record integrity guard denies
strict credit in every arm. The record-authority criterion follows
operative paragraph 13, which urges investigations within the
States' jurisdiction and urges action where appropriate. Freeze
the verbatim query as the targeted retrieval baseline. Require
accurate preservation of the operative verb and an explicit
speaker, action and recipient before treating the full-record
score as a reward for a communication policy.

The CPU run produced 42 generations with zero model updates.
This is one meeting, four authored requests, and one same-assistant
review of 17 distinct final texts and evidence views. Arm names
were removed from the review items and the scorer validates their
exact spans. The review has no independent rater. Peer, independent,
and solo each have 12 calls under the per-task accounting. The
verbatim arm has eight calls, and the direct controls each have
four. Shared openings and independent selections were run only
once per identical request. Actual input and output tokens are in
the results. [Scores and attribution](results.json) ·
[Arm-hidden review items](review-items.json) · [Exact accepted and rejected spans](grades.json)

Run from the reader-use directory in the Qwen3.5 environment.

```bash
PYTHONPATH=../../../../src python facilitator_requested_evidence_provenance.py
python facilitator_requested_evidence.py verify facilitator-requested-evidence
python facilitator_requested_evidence_score.py facilitator-requested-evidence --grades facilitator-requested-evidence/grades.json
```
