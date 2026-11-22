# Check the UNIFIL transfer against written records

Four paired witnesses compare the same historical blocks with and
without one delivered workshop sign. The deterministic writer uses
the delivered signs to certify a decision, list exclusions and label
a mandate as inferred or ambiguous. The scorer uses a local five-item
rubric with the same 70-point total and workshop release gate as v1.1.
Every final has quote-checked marks, including observed sign spans.
[Selection protocol](protocol.md) · [Added rubric](rubric.json) · [Signed evidence](public-proofs.json)

| Contrast | Before | After | Scored gain | Tree's predicted gain /70 |
| --- | ---: | ---: | ---: | ---: |
| Sign proves an impasse with an ambiguous mandate | 0 | 56 | 56 | 1.00 |
| Sign identifies one mandate after proof, with the other still ambiguous | 56 | 56 | 0 | 0.20 |
| Sign identifies the remaining mandate after proof | 56 | 70 | 14 | 0.20 |
| Sign proves a compatible option on a menu with several possible agreements | 0 | 56 | 56 | 0.80 |

A certified impasse can release with one unresolved mandate. In the first
witness, 4% delivery and the 0.035 send fee give an incremental normalized
return of −0.003. The tree values the reply as a complete record and
therefore expects a positive return. In the second witness, resolving
one of two unknown mandates still leaves the joint attribution
criterion unmet. In the third witness, adding information changes
the record without changing its first-line decision. All four trace
gains match the earlier proxy under these authored marks.
[Exact source marks](marks.json) · [Frozen-scorer output](scored.json)

This is a selective same-assistant check using deterministic text.
The frozen benchmark and the original transfer fit are unchanged.
[Official record and accession](../README.md)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 replay.py replay | cmp - public-proofs.json
python3 replay.py deck | cmp - deck.json
python3 replay.py score | cmp - scored.json
```

A separate frozen Qwen writer received the same eight public states.
It copied all decision lines correctly, and one final released.
The comparison distinguishes how much the signs support from what
free-form writing can preserve. [Live writer outputs and scoring](writer/README.md)
