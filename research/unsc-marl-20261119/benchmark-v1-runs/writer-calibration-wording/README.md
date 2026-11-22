# Test writer approvals after paraphrasing the sources

Both previously approved comparisons survived the paraphrases on
Resolution 2744. Reusing the old pair-level approvals and running
fresh source checks yielded the same six historical release scores.
The trained routing policy scored **40.411** against **39.457** for
the strongest arrival-only policy on the 96 held settings. These
scores include the simulation's send price and exclude inference
and review costs.

| Received pair | Compact writer result | Fresh source check | Released /70 |
| --- | --- | --- | ---: |
| Malta and committee authority | Supports the division of roles | Clears | 70 |
| A3+ and continuous review | Contrasts timing with the Council's stated intention | Clears | 70 |
| Malta and review | Proposes a comparison about review timing | Rejects | 52 |
| A3+ and committee authority | Proposes an unsupported link about decision roles | Rejects | 52 |
| Switzerland and review | Uses a document phrase as a delegate witness | Witness validation blocks | 52 |
| Switzerland and committee authority | Equates the Ombudsperson reference with the Annex I roles | Rejects | 52 |

The source-only paragraphs stay in the final record. The A3+ paragraph
states the preference for a time limit. The model's extracted witness
mentions only support for implementing ongoing review. The full
paragraph, together with the comparison connective and Council
paragraph, supplies the basis for the scored timing link.

The two new fictional cards reuse the previously approved pair
identities but reverse who decides a delisting request or whether the
A3+ favored a time limit. The writer tries to abstain using a malformed
type on the authority reversal. It produces a nonverbatim quote on
the review reversal. Both fall back during witness validation before
the semantic gate. This result measures genuine paraphrases and
malformed reversal outputs. An earlier fictional review reversal
did produce a neatly formatted false link. [Earlier reversal replay](../delisting-witness-render/README.md)

One frozen Qwen3.5-4B worker ran eight writer calls and 14 distinct
label evaluations on a 12-thread AMD EPYC 9575F 64-Core Processor.
There were 20 logical label evaluations, with byte-identical
requests reused during the run. The fresh calls used 5,614 input
tokens and generated 432 writer tokens. Source spans, marks and
policy scores are retained. The evaluation uses one reader and
one exposed docket. It gives evidence for this paraphrase set and
leaves broader robustness open.

[Protocol](protocol.md) · [Locked source cards](plan.json) ·
[Actual outputs and decisions](evidence/episodes.json) ·
[Token verification](verified.json) · [Marks and source spans](marks.json) ·
[Policy replay](results.json)

Run in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B probe.py plan | cmp plan.json -
python -B probe.py verify | cmp verified.json -
python -B probe.py score | cmp results.json -
```
