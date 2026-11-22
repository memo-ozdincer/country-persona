# Transfer the certified workshop dialogue to Iraq

Two cases and both speaker orders run with frozen Qwen3.5-4B. Each
role receives its own fictional mandate. The opener states a typed full
requirement. The other role sees that declaration and supplies its own
when one answer can complete a proof. Each of the eight declarations
matches its own card. The public ledger certifies A in both overlap
orders and impasse in both conflict orders. The frozen Syria router also
ranks the second role first in all four initial observations. The
proof-relevance rule already identifies a unique eligible recipient in
each case. This test gives no additional evidence of learned routing
benefit over that rule.
[Protocol](protocol.md) · [Live role-local requests and evaluation](evidence/episodes.jsonl)

| Writer input | Exact v1 decisions /4 | Correct with package-prefix alias /4 | Released records /4 | Released points /280 |
| --- | ---: | ---: | ---: | ---: |
| Independent notes | 0 | 2 | 2 | 112 |
| Typed notes | 0 | 2 | 2 | 84 |
| Same typed notes with a certificate | 2 | 4 | 3 | 168 |

The three arms each use two delegate calls and one writer call per
condition. The typed arms share the actual delegate calls. Their final
prompts differ only by the computed certificate. With the certificate,
both impasse records give the right decision, while both agreement
records say `Decision: PACKAGE-A`. The frozen release parser accepts
`Decision: A`. The alias diagnostic isolates this presentation error
while preserving the reported v1 outcome. The certificate writer also
puts the delegates' workshop constraints under “Historical Context”
in one impasse record. That leaves its authority guard uncertain.
Neither proof nor header correctness guarantees a complete record.

The independent arm uses 6,364 input tokens across four conditions,
compared with 4,055 for typed notes and 4,413 with a certificate.
The frozen v1 task allows 150 words per final record, and the same
token ceilings apply across the arms. The supplied public materials
and task preserve the adopted 31 May 2024 expiry and the separate
31 March 2024 review deadline. The scope and authorship criteria
remain in the same-assistant review.
[Opaque scoring packets](deck.json) · [Exact-span judgments](marks.json) · [Final and action scores](results.json)

## Clarify the writer's first line

A dependent replay replaces the ambiguous `PACKAGE-ID` instruction
with the six literal values allowed by the frozen parser. The replay
keeps the notes, certificate and source materials fixed. All four fresh
finals pass mechanical scoring and the authority guard. Released points
rise from 168 to 210 of 280. One overlap final earns all five content
criteria. The other three omit the historical unanimity, and both
impasse finals also omit the documentation choice. The result separates
certificate success, exact disposition, and completeness of the prose.
[Format protocol](format-protocol.md) · [Unedited records](format-evidence/records.jsonl) · [Final rubric scores](format-results.json)

Both passes used NVIDIA RTX PRO 6000 Blackwell Server Edition. The initial
pass makes 28 physical calls and the dependent pass makes four. Prompt
and token receipts replay with zero optimizer updates. The review is
same-assistant, the docket has prior project exposure, and the format
change was selected after inspecting the initial records. The format
intervention lives outside the frozen v1 contract. This transfer tests
a structured communication protocol and the use of a decision
certificate by a frozen writer.
[Initial verification](verification.json) · [Format verification](format-verification.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python transfer.py verify | cmp verification.json
python score.py deck | cmp deck.json
python score.py score | cmp results.json
python format_replay.py verify | cmp format-verification.json
python score_format.py deck | cmp format-deck.json
python score_format.py score | cmp format-results.json
```
