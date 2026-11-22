# Plan one UNIFIL question under public uncertainty

The chair can ask either role about any package or stay silent.
It averages the two possible verified signs under a uniform
prior over each role's still-compatible single-field mandates.
After a question, the delegate uses its own mandate to pass
or send. Public request selection matches in all 74 repeated
observations across the three fictional worlds and two modeled
delivery rates. The frozen tree was fitted on synthetic worlds.
[Protocol](protocol.md) · [All aggregate arms and divergent paths](route.json)

| Policy at 0.80 delivery | Questions | Replies | Expected new proofs | Expected record gain | Net gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exact decision-oriented rule | 400 | 322 | 257.60 | 227.36 | 200.09 |
| Exact record-aware rule | 496 | 414 | 257.60 | 242.08 | 207.75 |
| Learned chair and exact responder | 498 | 414 | 257.60 | 242.08 | 207.67 |
| Learned chair and responder | 498 | 416 | 257.60 | 242.08 | 207.60 |

The record-aware rule spends more on attribution and gains 7.66
net over the decision rule under the declared one-item proxy.
Both learned versions reach the same expected record gain. An
exact local responder withholds two unnecessary replies, but
the learned chair already incurred their question costs. At
0.08 delivery the exact record-aware rule asks 53 times and
earns 0.265. Both learned variants ask 94 times and earn −0.154.
The 41 additional questions come from over-valuing partial
impasses. Silence has zero incremental value.

These are 768 opening-world presentations per delivery setting,
from repeated signs and only one historical family. The oracle
uses the same public prior as the learned router. Reported gains
replay actual sampled-world signs rather than averaging over
the chair's assumed prior. The related [final-record witnesses](../record-check/README.md)
check the proxy on selected written cases. This audit does not
use newly written records to score all openings.

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 route.py | cmp - route.json
```

A four-call diagnostic receives the two extra learned queries and two
productive controls. All four replies are valid. Only the two controls
add released rubric credit. [Live reply and record evidence](live/README.md)
