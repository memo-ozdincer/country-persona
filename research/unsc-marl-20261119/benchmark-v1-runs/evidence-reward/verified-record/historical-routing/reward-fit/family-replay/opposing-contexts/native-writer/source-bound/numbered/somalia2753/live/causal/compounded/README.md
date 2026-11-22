# Preserve the U.S. objection inside the addressed message

The previous assigned U.S. reply selected its support for the resolution
and conditions review while dropping its objection to fewer reports.
This follow-up groups that vote and reporting reservation into one
selectable unit. It reuses the other three raw actor responses and
the observed action sequence. The new prompt has the same right-desk
inventory, prior China send and heard U.S. question.

| Transport and encoding variant | Interval team | Query erased | Interval fixed | Fixed U.S. |
| --- | ---: | ---: | ---: | ---: |
| Original addressed reply | 56 | 56 | 56 | 56 |
| Compound reply, strict parser | 56 | 56 | 56 | 56 |
| Same compound reply after fence-only replay | 70 | 56 | 56 | 70 |

The one fresh Qwen3.5-4B reply selected the compound and the optional
secondary passage in a JSON Markdown fence. The original parser rejects
the wrapper. The separate format replay strips the one enclosing fence,
validates both selected IDs and expands the compound into the original
two positions. The unedited assembler fits the resulting three-card
record in 150 words and includes the U.S. reporting objection. The
interval team has the same message fee as the fixed U.S. target and
the query-erased arm. Its fee is 0.05 higher than the interval fixed arm.

The successful row is a targeted, post-failure repair and a post hoc
format replay. The selected branch shows how preserved content makes
the addressed question consequential. A fixed U.S. target gives the
same observed result. All other native outputs, routing decisions and
message costs are held fixed. One fresh call ran on an NVIDIA RTX PRO
6000 Blackwell Server Edition with frozen weights. This evidence is
limited to the exposed Somalia branch and same-assistant source marks.
[Compound protocol](protocol.md) · [Raw call](evidence/calls.jsonl) ·
[Strict result](results.json) · [Fence protocol](fence-protocol.md) ·
[Final records and source marks](fenced-results.json) · [Native verification](verification.json)

```bash
set -o pipefail
python3 compound_reply.py plan | cmp - plan.json
python3 compound_reply.py verify | cmp - verification.json
python3 compound_reply.py score | cmp - results.json
python3 fenced_replay.py dispatch | cmp - fenced-dispatch.json
python3 fenced_replay.py score | cmp - fenced-results.json
```

[Native token constraints](structured/README.md) eliminate the syntax
failure and reveal a content regression. The accompanying simulator
tests routing policies that account for valid but incomplete replies.
