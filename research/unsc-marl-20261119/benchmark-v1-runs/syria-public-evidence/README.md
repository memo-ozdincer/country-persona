# Certify an impasse from public workshop notes

Frozen Qwen3.5-4B read 14 distinct archived Syria notes and eight matched
stress notes. Each request contains the public note, its speaker, the
field dictionary and the workshop options. Private cards remain on the
evaluation side. The reader returns a quoted constraint and endorsement
or null for either field. All 22 outputs passed the JSON schema check.
The same decision ledger handles every admitted claim. It certifies
a recommendation only when both participants endorse it and certifies
an impasse when the notes exclude every option.
[Protocol](protocol.md) · [Requests](requests.json) · [Reader responses](evidence/extractions.jsonl)

| Method | Supported deferrals on archived overlap /4 | Correct certified impasses /4 | Matched stress notes /8 |
| --- | ---: | ---: | ---: |
| Balanced learned chair | 1 | 4 | — |
| Reader and literal-quote gate | 3 | 2 | 6 |
| Reader and strict source gate | 4 | 0 | 8 |
| Reader with containing-clause recovery | 4 | 1 | 8 |
| Direct scan of explicitly owned binding clauses | 4 | 2 | 8 |
| Ledger replay with existing same-assistant marks | 4 | 4 | — |

The literal gate admits a proposed six-month term as a binding mandate
and an explicit UK mandate in a note from Brazil. The stricter gate
rejects both. It also filters valid short citations such as
`duration = six` when the speaker and modality appear outside the
selected span. Checking the containing clause recovers one projected
impasse. Directly scanning such clauses without requiring a model
constraint recovers the second projected impasse. That scan still uses
the original source-gated model endorsements. Both recovery methods
reject a short exact quote from a negated claim. The stress examples
share the archive's vocabulary and were fixed before inference.
[Admission and ledger replay](results.json) · [Dependent recovery protocol](recovery-protocol.md) · [Recovered spans](recovery.json)

The direct scan misses both impasses from raw notes. The Brazil-first
opening only connects its proposal to its constraint across sentences.
The UK-first reply mentions the peer proposal and its own stricter
duration in one mixed-scope passage. An explicitly owned clause rule
recovers neither complete pair. The raw Brazil-first overlap still has
a locally false UK endorsement in the admitted claims, giving seven of
eight note pairs with all claims consistent with the hidden mandates.
The chair correctly defers on this pair because it sees no certified
mutual support. Public sufficiency and private truth therefore retain
separate evaluation fields.

The 22 calls used one NVIDIA RTX PRO 6000 Blackwell Server Edition.
Prompt, token and completion replay verify the inference artifacts.
No model was updated. The recovery was developed after seeing the
results on one exposed family. It is a rule for this workshop's field
dictionary and leaves reliable general evidence extraction open.
[Run receipt](evidence/launch.json) · [Verification](verification.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
python reader.py deck | cmp requests.json
python reader.py verify | cmp verification.json
python admit.py | cmp results.json
python recover.py | cmp recovery.json
```
