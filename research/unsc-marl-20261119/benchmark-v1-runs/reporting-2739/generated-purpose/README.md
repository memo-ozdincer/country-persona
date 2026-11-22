# Generate the shared purpose and preserve source attribution

**The generated phrase filled the missing comparison on Resolution 2739.**
Both model outputs with the complete evidence pair say “to keep the Council
informed.” The fixed template attributes that purpose to the co-sponsors and
Algeria and preserves the abstention. The assistant-reviewed briefs earn
70/70 in both orders, up from 56/70 for the fixed facts and the earlier
free-writing chair. The phrase is verbatim model output. The author supplies
the comparison type, actors, and vote framing. [Candidate text and scores](scores.json)

| Evidence and order | Unrestricted candidate /70 | Require exact full pair /70 | Full pair plus averaged verifier /70 |
| --- | ---: | ---: | ---: |
| Both statements, co-sponsors first | 70 | 70 | 56 |
| Both statements, Algeria first | 70 | 70 | 56 |
| Public action and Algeria, action first | 0 | 49 | 49 |
| Public action and Algeria, action second | 0 | 49 | 49 |

In both crossed views the generator returned the same phrase even though
only Algeria's position was in evidence. Requiring the two registered
source identities and their exact previously extracted quotes kept the
unsupported comparison out of the record. On its own this gate
checks provenance and the presence of necessary source spans. It gives no
guarantee about a different generated phrase.

The unchanged binary verifier rejected both correct composed candidates
at mean margins −0.4375 and −0.25. It accepted the unsupported
action-second version at +0.5625. The exact-pair rule still blocked
that release. The earlier verifier had accepted a different authored
formulation of the same supported relation. This tests the verifier on
model-generated content and shows a failure that the authored probes
did not expose. [Exact decisions and prompt replay](verified.json) · [Assistant grades](marks.json)

## Consequence for cooperative send decisions

Rescore the same 64 exploratory exchanges using both deployment rules.
With the mechanical gate, the target critics recover a 14-point joint
bonus in both orders and choose to send both sources in all 12 held
transport settings. Mean simulated utility is **47.135**, compared with
42 for withholding. Always sending both reaches the same utility on this
grid. When the verifier also gates release, the bonus disappears. The
refitted critics withhold on every setting and utility falls back to 42.
These are simulations reusing the graded outputs, with the same
constructed send cost as the previous study. That cost excludes LLM
calls. [Replay and per-setting utility](fit-replay.json)

Four generation calls and eight first-token verification calls use 4,116
input and 40 saved output tokens on Aurora's NVIDIA RTX PRO 6000 Blackwell
Server Edition. A complete-pair path uses 982 new input tokens plus 338
if the earlier extraction calls are charged. The verifier results can be
replayed separately from the mechanical gate and were collected on both
crossed views for the diagnostic. Outputs and tokens replay exactly.
The model is frozen and the scoring labels are assistant annotations on
one exposed event. The positive result demonstrates a generated phrase
in a case-specific, source-matched composition. Unseen-docket
deliberation and a portable release policy remain unverified.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B purpose_study.py plan | cmp plan.json -
"$python" -B purpose_study.py verify | cmp verified.json -
"$python" -B annotate.py | cmp marks.json -
"$python" -B assess.py | cmp scores.json -
"$python" -B fit_replay.py | cmp fit-replay.json -
```

[Locked protocol](protocol.md) · [Earlier quote-assisted writer](../quoted-purpose/README.md) · [Earlier verifier probes](../../relation-support-transfer/README.md)
