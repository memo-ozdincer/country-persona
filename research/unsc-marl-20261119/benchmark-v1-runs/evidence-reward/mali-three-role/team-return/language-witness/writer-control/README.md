# Writer controls on the pivotal Mali case

Both frozen Qwen3.5-4B controls receive the same eight public evidence
blocks. The original record hit its token cap with an incorrect
deferral. The length-only control keeps the exact prompt and raises
the token ceiling. The proof-first control keeps the original ceiling
and moves the known requirements and menu ahead of the historical
record. It explicitly allows certifying an impasse with an unknown
condition when the known conditions already exclude every option.

| Writer condition | Output cap | Words | Header | Released /70 |
| --- | ---: | ---: | --- | ---: |
| Original | 280 | 198 | Unresolved | 0 |
| More tokens | 420 | 286 | Unresolved | 0 |
| Proof first | 280 | 209 | Impasse | 0 |
| Deterministic application control | — | 147 | Impasse | 56 |

The longer answer finishes but exceeds 225 words. It explicitly reasons
that the known conditions leave an option available. The proof-first
draft gives the correct decision. It claims incorrectly that option A's
written note conflicts with the written-note requirement and that D
lacks open circulation. It reaches the output limit before stating the
second vote tally. Both controls are adaptive, single-witness
diagnostics. The model is unchanged and the same assistant annotated
both records with source spans.

[Protocol](protocol.md) · [Native outputs](evidence/calls.jsonl) ·
[Span-backed marks](marks.json) · [Scored results](results.json) ·
[Token verification](verification.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 controls.py deck | cmp - requests.json
python3 check.py packets | cmp - packets.json
python3 check.py verify | cmp - verification.json
python3 check.py score | cmp - results.json
```
