# Compose source-checked records from learned-team transcripts

Two completed learned-team trajectories provide the public requirements
for the Mali and Cyprus impasses. The same workshop proof is appended
to an exact-span historical record. The native model receives only the
historical source blocks and descriptions of the fields to recover.
The compiler accepts a field only when an exact contiguous candidate
span occurs in its assigned source and satisfies the docket's frozen
pattern. The renderer uses the matched source values and verified
public workshop state. Missing fields remain missing. On Mali the
meeting date comes from the pinned dated case metadata.

Direct regex extraction from the assigned source is the matched
model-free control. It uses the same field patterns and renderer.
Three further checks for each available field reject a fabricated
suffix, a quote copied from another field's source and an exact but
incomplete fragment. A separate missing-source control refuses to
admit a real Cyprus vote quote from the full packet when its source
is withheld. A fabricated count is also rejected. These are source
identity and completeness checks within two authored contracts.
They depend on the quality of the supplied source packets and on
the correctness of the patterns.

The first preflight caught invalid JSON escaping in the regular
expressions. It was corrected before any model call. The field
contract and prompts were frozen before native collection.
[Protocol](protocol.md) · [Field contracts](contracts.json) ·
[Software checks](software.json)

## Native results

Frozen Qwen3.5-4B recovered all four fields on both full packets.
The resulting Cyprus and Mali records are byte-identical to
direct extraction. When the Cyprus vote block was absent, Qwen
proposed a procedural sentence from the positions block as the
vote. The compiler admitted no vote claim and preserved the other
three fields. All three calls finished on NVIDIA RTX PRO 6000
Blackwell Server Edition. There were no model updates.

| Packet | Native admitted fields | Words | Native release / 70 | Direct release / 70 |
| --- | ---: | ---: | ---: | ---: |
| Mali | 4 / 4 | 152 | 56 | 56 |
| Cyprus | 4 / 4 | 126 | 70 | 70 |
| Cyprus vote withheld | 3 / 4 | 108 | 42 | 42 |

The Mali cap on attainable points in this state follows from one
unknown fictional desk condition. The withheld Cyprus packet
loses the vote criterion and the item that distinguishes the
Council vote from party agreement. All three composed records
clear the material source guard under the same assistant's
span-backed marks. Removing either decisive reply from either
transcript forces a deferral in the software audit. Direct
extraction ties the native selector on every selected packet.

[Native proposals](evidence/calls.jsonl) · [Scoring packets and outputs](packets.json) ·
[Marks](marks.json) · [Scores](results.json) · [Native trace replay](verification.json)

## Replay the final-record score over delivery branches

The [scoring replay](scoring-replay.json) composes records through
the v1.2 scorer across all eight worlds and every modeled delivery
branch, using the two hand-reviewed source contracts. It holds
admitted source fields fixed. On Cyprus at 90% per desk and two
questions, the learned team averages **28.35 released points**
versus 14.18 with fixed-order mandatory replies and zero with
silence. The same fitted chair with mandatory replies also earns
28.35, at higher cost. At a 35% Access delivery rate the learned
team's two-question net is −0.0365, below fixed order's −0.0300
and silence at zero. With the Cyprus vote source absent, the
learned team loses to silence in four of six modeled conditions.
The learned controller does not receive source availability.
This is an expected score on two exposed, structurally related
workshops under stipulated delivery, with procedural rubric marks
for compiler output. It adds no new native dialogue or independent
semantic review. [Replay protocol](scoring-replay-protocol.md)

Replay from this directory with the project Python and NumPy,
Jinja and tokenizers.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 record.py requests | cmp - requests.json
python3 record.py direct | cmp - direct.json
python3 check_record.py software | cmp - software.json
python3 check_record.py verify | cmp - verification.json
python3 check_record.py packets | cmp - packets.json
python3 check_record.py score | cmp - results.json
python3 scoring_replay.py | cmp - scoring-replay.json
```

[Training with the available source value](source-aware/README.md)
improves all six vote-withheld net results. Public model-based selection
between the frozen teams and silence prevents losses when rates are
correctly specified in the tested matrix. Losses return when delivery
degrades while the selected policies keep their original rates.

[Runnable learned-team workshop](runtime/README.md) connects the saved
policies, scoped replies and checked source compiler. It reproduces the
two scored impasses, checks lossy or invalid replies, and evaluates both
fitted teams on an exhaustive three-option holdout.

[Resolution 2422 historical routing](historical-routing/README.md)
uses source-checked desk receipts without fictional mandates. A compact
record reaches 70/70 when all parties' evidence arrives. The existing
learned router gains against same-responder silence and trails the fixed
request for Serbia's evidence under the full v1.2 rubric.
