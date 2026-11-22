# Check whether the UNIFIL writer preserves certified and uncertain evidence

Frozen Qwen3.5-4B wrote all eight final records from the same four
selected public witness pairs used by the deterministic reference.
The prompt supplied the verified decision, signed claims and public
lists of possible mandate requirements. It contained no private
cards. The selection includes two states that correctly defer because
the proof is incomplete.

| Additional public evidence | Deterministic points, before → after | Qwen points, before → after |
| --- | ---: | ---: |
| Adds a proof of impasse with one mandate ambiguous | 0 → 56 | 0 → 28 |
| Identifies one of two ambiguous mandates after proof | 56 → 56 | 0 → 0 |
| Identifies the last mandate after proof | 56 → 70 | 0 → 0 |
| Proves a compatible package when several are possible | 0 → 56 | 0 → 0 |

All eight responses follow the supplied decision line. Only one
releases under the rubric. Six have failed source guards and one has
an uncertain guard. In one impasse, for example, the writer turns
China's public exclusions of A and C into an exclusion of the oral
option B. In the multiple-agreement case, it interprets both roles
accepting A as proof that their mandates are identical and uniquely
known. Each role still has two plausible mandates at that point.
In the fully attributed impasse, it gives both correct conditions
but also describes a briefing vote absent from the transcript and
says the full requirement remains ambiguous. This is the uncertain
guard case.

The only released Qwen response scores 28/70. It gets the workshop
proof and historical disposition, but leaves out the positions
criterion, the qualified national disagreement, and the complete
authority clause. These are same-assistant semantic marks. All eight
raw responses are available for independent review. The eight calls
ran without optimizer updates on NVIDIA RTX PRO 6000 Blackwell
Server Edition. These witnesses hold the proof policy fixed and
test the final prose. They do not estimate overall model performance
on UNIFIL.
[Protocol](protocol.md) · [Raw responses](evidence/records.jsonl) · [Judge deck](deck.json) ·
[Rubric marks](marks.json) · [Scores](results.json) · [Token verification](verification.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python collect_writer.py deck | cmp - requests.json
python grade.py deck | cmp - deck.json
python grade.py score | cmp - results.json
python grade.py verify | cmp - verification.json
```
