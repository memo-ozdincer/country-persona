# Live Mali proof and record replay

A previously fitted router used five frozen Qwen3.5-4B replies on
NVIDIA RTX PRO 6000 Blackwell Server Edition. The workshop uses fictional
role cards and narrow yes/no answers. All five replies were complete and
matched their private cards. The runtime admitted a sign only after checking
it against that typed requirement. The next question used the resulting
public state. All five live messages were delivered. The planner's 0.90
delivery assumption was used for selecting questions.

| Selected world | Public replies | Released score by phase |
| --- | --- | --- |
| Agreement on package B | Russian drafting desk, French drafting desk, Secretariat technical desk | 0 → 0 → 0 → 70 |
| Impasse with French requirement unknown | Russian drafting desk, Secretariat technical desk | 0 → 0 → 56 |

The first episode had a three-question cap. The second had a two-question
cap. In the second episode, the known exclusions cover the whole menu.
The missing requirement costs the positions criterion. A longer cap can
make that additional attribution worth pursuing. The checkpoints before
certification retain 28 raw points for open issues and authority and
cannot release a complete-world decision.

[Protocol](protocol.md) · [Native replies](evidence/episodes.jsonl) ·
[Rendered records](deck.json) · [Span-backed assistant marks](marks.json) ·
[Scores](results.json) · [Token verification](verification.json)

The historical prose and the public-state workshop text were written by a
deterministic renderer. This verifies two selected dialogue paths and their
resulting documentary records. The semantic marks are the same assistant's
annotations. Qwen produced the signs and had zero optimizer updates.

Run the following from this directory.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 live.py deck | cmp - opening-requests.json
python3 review.py deck | cmp - deck.json
python3 review.py score | cmp - results.json
/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python review.py verify | cmp - verification.json
```
