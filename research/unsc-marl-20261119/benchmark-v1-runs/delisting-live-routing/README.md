# Execute the 2744 routing policies with fresh model calls

The learned reply desk gained **2.304 released points** over the
best arrival-only desk under each held prior. Both arms always
attempted delivery of the opening note, so their sending costs were
equal. The advantage came from using the received note to choose
between the two document excerpts.

| Opening-note distribution | Learned release /70 | Arrival-only release /70 | Learned utility | Arrival-only utility |
| --- | ---: | ---: | ---: | ---: |
| 60% Malta, 20% A3+, 20% Switzerland | 56.816 | 54.512 | 48.816 | 46.512 |
| 20% Malta, 20% A3+, 60% Switzerland | 52.208 | 49.904 | 44.208 | 41.904 |

Delivery is 80% in each direction and a send costs eight points.
The runner enumerates all 48 weighted branches across the two
systems and two priors. It runs frozen policies on the local
observations made available in each branch. The learned desk reads
an arriving note with a two-label verifier before selecting a
document. Arrival-only chooses its reply from receipt or silence.
The same chair receives the surviving excerpts in each arm and
constructs a compact record with its own source gate. The fresh
writer and verifier recover both supported links, leave all four
crossed pairs unlinked and retain the public disposition. The separate software
audit confirms that unavailable text never appears in the record,
the reply does not depend on the return delivery outcome, and
re-optimizing arrival-only on the fresh pair scores leaves both
baseline values unchanged.

The cached comparator uses the archived score table to set its
actions before model execution. The live runner initializes its
inference cache empty and reuses only byte-identical requests made
during this run. It does not consume stored logits or stored prose.
The logical rates count repeats so the execution cache does not hide
cost. Both arms average 0.64 writer calls. The learned arm uses
4.16 label evaluations per episode. Arrival-only uses 2.56 and
0.512 label evaluations under the two priors. Input token overhead
is 344.704 and 793.344 respectively. If only extra input tokens
were priced, the two gains would break even at about 6.68 and
2.90 points per thousand additional input tokens. The reported
utilities include the simulated sending cost and exclude inference.

The worker used a single AMD EPYC 9575F 64-Core Processor with 12
threads, and frozen Qwen3.5-4B in BF16. The trial executes one
exposed docket with supplied excerpts, a simulated channel and a
project-authored relationship key. Transfer to other dockets,
learner benefit from suppressing an opening, and native deliberation
quality remain outside this test.

[Locked protocol](protocol.md) · [Policies and fingerprints](plan.json) ·
[Model requests and token traces](evidence/calls.jsonl) ·
[Final records and actions](evidence/episodes.json) · [Token verification](verified.json) ·
[Replay audit](audit.json) · [Inference usage](usage.json)

Run these checks in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B live.py plan | cmp plan.json -
python -B live.py verify | cmp verified.json -
python -B audit.py | cmp audit.json -
python -B costs.py | cmp usage.json -
```
