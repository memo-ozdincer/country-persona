# Generate the transport receipts during a Somalia route

Two selected Somalia branches execute the interval team, the same
team with the question erased, the equally informed interval fixed
policy, and a fixed request for the U.S. card. The controllers operate
on numeric observations. Qwen3.5-4B realizes each selected role card
with fresh passage IDs. Openers see their own inventories. The
responder also sees its earlier attempted send and the heard query.
The assembler only uses admitted cards.

| Selected branch | Interval team | Query erased | Interval fixed | Fixed U.S. |
| --- | ---: | ---: | ---: | ---: |
| U.S. opening erased | 49 | 49 | 42 | 49 |
| Hearing the question changes the transmitted card | 56 | 56 | 56 | 56 |

Each cell is a released score out of 70. In the first branch the
interval team recovers the erased U.S. opening. The responder also
sends the card after question erasure. The fixed U.S. target uses the
same prompt and output on this branch.

In the second branch the responder sends the U.S. card when it hears
the question and repeats the Somalia card under erasure. The received
U.S. card contains its vote and support for reviewing conditions. It
omits the objection to fewer reports and briefings. Both the U.S.
position and the China–U.S. distinction therefore remain incomplete.
The addressed turn changes the source receipt and costs 0.05 more than
the interval fixed arm, while all four records receive the same grade.

The search found 15 clean modeled branches where hearing the question
raises the final grade above erasure and the original interval fixed
policy. Optimizing fixed responders directly on same-inventory
triplets removes all qualifying adaptive triplet wins in the
searched clean cases. The single live branches demonstrate different
mechanisms and allow a narrowly targeted fixed request to match the
best observed record.

Across 18 modeled conditions on the archived score bank, erasing the
query while charging its cost reduces raw release by 0.3939 points
and net by 0.4277 on average. The intact team wins 17 of 18 against
erasure with one tie. Swapping either component with its interval
fixed counterpart lowers average net. This is evidence about the
modeled team and holds the final record's expected card value fixed.
The second live branch shows why that assumption needs checking.

Foreign and repeated IDs in a replayed U.S. reply still incur the
attempted message fee. Neither fault enters the record. Native
tokens, raw responses and logical messages are sealed separately.
Each of these two runs uses four fresh calls on an NVIDIA RTX PRO
6000 Blackwell Server Edition. Same-assistant checks apply to the
exposed rubric and author-built passage menus. Delivery losses are
scripted.
[Protocol](protocol.md) · [Native trace](evidence/dispatch.json) ·
[First scores](results.json) · [Causal protocol](causal/protocol.md) ·
[Causal trace](causal/evidence/dispatch.json) · [Causal scores](causal/results.json) ·
[Erasure and component swaps](mechanism-results.json) ·
[Matched context audit](matches.json) · [Query witness search](query-witnesses.json)

Run in the parent Python environment.

```bash
set -o pipefail
python3 match.py | cmp - matches.json
python3 mechanism.py | cmp - mechanism-results.json
python3 identify_query.py | cmp - query-witnesses.json
python3 live_somalia.py plan | cmp - plan.json
python3 audit_live.py verify | cmp - verification.json
python3 audit_live.py score | cmp - results.json
python3 fault_replay.py | cmp - faults.json
(cd causal && python3 causal_live.py plan | cmp - plan.json)
python3 audit_live.py verify --causal | cmp - causal/verification.json
python3 audit_live.py score --causal | cmp - causal/results.json
python3 fault_replay.py --causal | cmp - causal/faults.json
```

[Grouped U.S. reply](causal/compounded/README.md) tests subject-matter
completeness at the source encoder. The model selects the complete
position in a Markdown fence. A separate format-only replay restores
70 points versus 56 with question erasure.
