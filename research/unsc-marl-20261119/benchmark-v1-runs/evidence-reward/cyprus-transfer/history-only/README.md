# Attach a native historical paragraph to the verified public proof

The composed record keeps the exact impasse line, public roles and
exclusions, unknown scheduling requirement and workshop authority.
The same frozen Qwen3.5-4B checkpoint writes a 66-word historical
paragraph from the four source blocks. The 120-word record appends
the paragraph unchanged. No language-model parameters are updated.

The record passes the mechanical decision check and earns 56/70
raw points. It omits the UK's sponsorship and the exact vote count.
The source confirms the representatives maintained their positions
and provides no report of a settlement. The generated sentence may
instead attribute an explicit finding of no settlement to the
President. The conservative source guard is uncertain, which yields
zero released points. The deterministic application control earns
70/70. Compared with free-form writing, the hybrid preserves the
proof and mandate chronology, while attribution and completeness
still require source review.

[Protocol](protocol.md) · [Unedited record](record.json) · [Span-backed mark](mark.json) ·
[Release score](results.json) · [Native verification](verification.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 compose.py request | cmp - request.json
python3 compose.py record | cmp - record.json
python3 review_composed.py verify | cmp - verification.json
python3 review_composed.py packet | cmp - packet.json
python3 review_composed.py score | cmp - results.json
```
