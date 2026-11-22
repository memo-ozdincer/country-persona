# Compare a learned reply gate with always sending

The selected worlds share an opening question for the Russian drafting
desk and its answer that circulation must be open. That answer makes A
and B unavailable. Both runs then ask the Secretariat technical desk.
Only its fictional requirement varies. A written-note requirement
excludes C and D and certifies an impasse. An oral-briefing requirement
excludes neither C nor D. The French timing requirement is still unknown.

The saved reply head sends in the first world and withholds in the
second. The always-send control uses the same fitted chair, query cap,
private requirements and reply generator. At 0.03 per send attempt,
the withheld reply saves 0.03 in the optional case. The workshop fee
does not include the cost of reading a historical packet or writing a
final. Withheld replies are not admitted as evidence.

[Protocol](protocol.md) · [Selected fully delivered routes](preview.json)

The first preflight imported another module named `review` and stopped
before model collection. The run loads the archived renderer from its
specific file path.

## Observed outcome

Two previously collected frozen Qwen3.5-4B signs match the exact
requests for the opening and the pivotal technical reply. The
always-send control collects the alternate technical reply and receives
the expected `N`. A new writer sees only the public sources, menu and
admitted signs. The pivotal writer request is identical in both arms
and uses one model generation. Four physical model calls produce the
one alternate sign and three unique final records on NVIDIA RTX PRO
6000 Blackwell Server Edition.

| World and arm | Attempts | Public decision | Native raw / released | Compiled raw / released |
| --- | ---: | --- | --- | --- |
| Pivotal, learned | 2 | Impasse | 0 / 0 | 56 / 56 |
| Pivotal, always send | 2 | Impasse | 0 / 0 | 56 / 56 |
| Optional, learned | 1 | Unresolved | 0 / 0 | 28 / 0 |
| Optional, always send | 2 | Unresolved | 14 / 0 | 28 / 0 |

Both optional arms leave the exact same compatible packages, C and D.
The extra reply adds an attributed fact while changing neither the
remaining options nor the decision. The deterministic record preserves
the fact when available. The complete-world score releases zero for a
deferral. The public certification column distinguishes a warranted
deferral from the pivotal writer's decision error.

All three unique native drafts begin with `Decision: UNRESOLVED`
and hit 280 tokens. They spend most of the budget on the historical
votes. The span-backed assistant review also marks them for assigning
the joint orderly drawdown rationale to France as a direct statement.
The official packet gives that rationale in the UAE's account of the two
sponsors. The matched deterministic renderer reaches 56/70 on the
pivotal state. This isolates what the public evidence already supports
from the frozen writer's use of that evidence.

[Native calls and responses](evidence/new-calls.jsonl) ·
[Full trajectories](evidence/episodes.jsonl) · [Scores](results.json) ·
[Token verification](verification.json) · [Writer controls](writer-control/README.md)

Run from this directory using the project Python with NumPy, Jinja
and tokenizers installed.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 witness.py preview | cmp - preview.json
python3 review_witness.py verify | cmp - verification.json
python3 review_witness.py packets | cmp - packets.json
python3 review_witness.py score | cmp - results.json
```
