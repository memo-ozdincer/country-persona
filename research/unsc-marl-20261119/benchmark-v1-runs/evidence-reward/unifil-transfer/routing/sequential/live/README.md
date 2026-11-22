# Execute two learned questions with live UNIFIL delegates

In each of three selected witness states, the learned planner issues
one question, waits for a verified Qwen3.5-4B reply, and chooses the
next question from the updated public log. The responder receives
one local prose card and the public signs. Its instructions require
an answer even when the sign will not settle the workshop immediately.
Each sign is admitted after a role-local truth check. Delivery is
complete in this live run. The model sees no other private card.
[Locked protocol](protocol.md) · [Actual prompts, replies and state transitions](evidence/episodes.jsonl)

| Witness | Replies in order | Final proof | Released points, opening → first → second |
| --- | --- | --- | ---: |
| Unique agreement | Brazil accepts A, then China accepts A | A | 0 → 0 → 70 |
| Impasse | Brazil excludes B, then Brazil excludes A | Impasse | 0 → 0 → 56 |
| Multiple possible agreements | Brazil accepts C, then China accepts C | C | 0 → 0 → 56 |

All six signs pass truth and format validation. The first reply
in each witness leaves the public outcome unresolved and earns no
released points. Each second reply completes a proof. In the last
two cases the evidence still leaves full mandate attribution
ambiguous for both roles. The compiled final brief states those
uncertainties and keeps the fictional exercise separate from the
official record. All nine record states are scored with exact-source
same-assistant marks. The one-step greedy policy would stay silent
at each opening in the paired replay.
[Final text and public evidence](deck.json) · [Rubric marks](marks.json) · [Scores](results.json)

The six native model calls used NVIDIA RTX PRO 6000 Blackwell
Server Edition. There are no additional optimizer updates. The
verified transcript includes each queried recipient, the exact
prompt rebuilt from prior accepted signs, the decoded reply and the
new public state. The openings come from a preselected diagnostic
deck. The experiment verifies a live two-turn continuation on those
states with a compiled final writer. It supplies no estimate of
overall diplomacy performance under live channel loss.
[Launch](evidence/launch.json) · [Native token and policy verification](verification.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python loop.py deck | cmp - opening-requests.json
python review.py verify | cmp - verification.json
python review.py deck | cmp - deck.json
python review.py score | cmp - results.json
```
