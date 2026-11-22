# Bind new language replies to individual sourced claims

Replay the same four UNIFIL and Myanmar branches and the same
visible passages as the live-writing experiment. Keep the
official vote, date, Council action and force of each operative
provision in a short reviewed public section. Test each
national claim against its own source. A single exact witness
can be reused in every view with the same source text.
A repeated card that already reached the chair preserves its
original opening passage for this check.

Qwen selects an exact contiguous excerpt or declines. The
literal gate verifies that the returned words are present.
The separate review checks whether that span establishes all
facts in the emitted claim, including actor, scope and role.
The system composes a record from approved clauses and
preserves a complete citation for each. Multi-source overlap
or disagreement requires both of its constituent findings.
An unsupported literal admission blocks release. The reviewed
arm withholds that clause and releases the supported partial
record. Each record is limited to 175 words.
[Locked protocol](protocol.md) ·
[Prior live replies and full-prose control](../facilitator-live-writing-evidence/README.md)

## Initial exact-witness results

Fourteen frozen-model calls produce nine exact witnesses that also
pass same-assistant support review. Two decline absent material.
All three presidency requests repeat the proposed claim in the
model's own words. The exact gate rejects those strings even though
the delivered passages contain both required facts. No incorrect
literal admission occurs on these measured prompts.

| Diagnostic branch | Learned live | Fixed request live | Independent live |
| --- | ---: | ---: | ---: |
| UNIFIL complementary evidence | 56 | 56 | 49 |
| UNIFIL all three sources | 70 | 70 | 70 |
| Myanmar presidency note available | 49 | 49 | 49 |
| Myanmar requested presidency note missing | 49 | 49 | 49 |

All 16 distinct assembled views are releasable. Three UNIFIL
views reach the strict 70-point record, including the learned live
receipt. Their full public section preserves the original adoption,
vote, mandate date and conditions. In the complementary branch,
the original China card restores the 7-point overlap and reaches
63. The live reply supports the objection and sovereignty point
without establishing China's support for the mission. China’s
support remains withheld in that view. The live UK reply also
omits sufficiently specific policy priorities in the script's
Myanmar branch. Its source-direct counterpart reaches 63 before
any role repair.

The fixed clauses and same-assistant support review define the
publication path. The 14 new witness calls use 2,050 input and
364 output tokens. They reuse the same live replies as the failed
free-form run. Generation cost and the review procedure differ
from that earlier writer. The experiment verifies a bounded
documentary workflow on selected exposed branches.
[Generated witnesses](transcript.jsonl) · [Exact reviews](marks.json) ·
[Initial assembled records](results.json)

## Retest the role evidence with sentence IDs

Replace the exact-quote instruction for the three rejected
presidency witnesses with a two-sentence selection. The model
names the sentence that supplies the President's procedural
announcement and the sentence that supplies India's national
explanation. It selects the correct pair in all three views
and returns `NONE` when shown only India's national explanation.
The selected contiguous text passes the same exact-source check.

On the Myanmar branch carrying the live presidency note, the
learned and independent records rise from 49 to 56. The scripted
record has no such note and remains at 49. The pooled Myanmar
record rises from 63 to 70. The full UNIFIL live record still
scores 70. The other gaps, including the omitted China support
and the UK reply's missing policy details, remain visible.

This post hoc interface change adds four actual model calls.
All selections were reviewed by the same assistant. The
public section and claims are prewritten, and the role repair
does not replace the routed replies or change their availability.
The selected branch results measure a documented publication
pipeline. They do not estimate population performance.
[Sentence-selection trace](role-ids/transcript.jsonl) ·
[Reviewed selections](role-ids/review.json) ·
[Final compiled records](role-ids/results.json)

```bash
python facilitator_live_claims_score.py facilitator-live-claims-evidence --marks facilitator-live-claims-evidence/marks.json
python facilitator_live_claims_role_ids.py score facilitator-live-claims-evidence/role-ids
```
