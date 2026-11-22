# Ask live delegates for the missing mandates

The rubric-weighted replay selects four follow-up contexts at 80%
modeled delivery. This experiment reuses those signed histories and
asks frozen Qwen3.5-4B for the receiving role's full fictional
mandate. The first stage, routing, renderer, and prior rubric marks
are fixed. The question and model response are fresh. The earlier
public signs are reconstructed, and delivery remains modeled.
[Initial protocol](protocol.md) · [Exact role-local requests](requests.json)

| Reply method | Admitted replies /4 | Expected released-point gain | Net gain after modeled cost |
| --- | ---: | ---: | ---: |
| Original Qwen prompt | 0 | 0.00 | −0.448 |
| Qwen with explicit extraction example | 4 | 35.84 | +0.064 |
| Deterministic extraction from the typed card | 4 | 35.84 | +0.064 |

All four replies to the original prompt returned a JSON object with
the right two keys. Each used the string `own_card` as the field
and copied the entire card as the value. The validator rejected all
four. Under the dependent prompt, the four unedited replies produced
the exact registered values `term=retain`, `documentation=public`,
`checkpoint=additional`, and `duration=nine`. Each passed role-local
validation. The public chair produced the same full-credit text as
the earlier replay on the branch where the reply arrives. The
deterministic extractor, limited to the registered card grammar,
produced identical final texts with zero Qwen calls.
[Initial raw replies](evidence/records.jsonl) · [Schema revision](schema/protocol.md) ·
[Clarified raw replies](schema/evidence/records.jsonl) · [All scored comparisons](schema/results.json)

At both modeled delivery rates of 0.80, a correct live declaration
recovers 14 points on a branch with probability 0.64. The four correct
declarations add 35.84 expected released points across the original
44 presentations and leave 16.80 expected correct decisions. The
extra cost is 0.448 in normalized rubric units. A single rejected
reply in this set would reverse the small net gain.

The four contexts come from the exact first sign. In the archived
forced-recipient comparison, the frozen native responder supplies that
sign in one context. The direct-credit adapter and the verified feature
head each supply it in two. The expected released-point gains from this
follow-up would then be 8.96 and 17.92, respectively, on these four
contexts alone. The other first-stage effects and stage-one costs
remain outside that splice. The expected-reward adapter reaches
none of the four. These are conditional compositions, rather than
fresh closed-loop rollouts.

The two dependent batches used NVIDIA RTX PRO 6000 Blackwell Server
Edition with no optimizer updates. The explicit example added 70
input tokens per call, and total generated tokens fell from 94 to 40.
Both model processes exited after sealing their output. The CPU
verification replays all eight exact prompts, stop tokens and decoded
responses. This is an exposed two-family protocol test with prior
same-assistant marks. The deterministic baseline establishes what the
typed format itself permits.
[Initial verification](verification.json) · [Clarified verification](schema/verification.json)

## Verify

Use the project's local Qwen environment for token verification.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python live.py deck | cmp - requests.json
python score.py verify | cmp - verification.json
python score.py score | cmp - results.json
cd schema
python clarify.py deck | cmp - requests.json
python compare.py verify | cmp - verification.json
python compare.py baseline | cmp - deterministic.json
python compare.py score | cmp - results.json
```
