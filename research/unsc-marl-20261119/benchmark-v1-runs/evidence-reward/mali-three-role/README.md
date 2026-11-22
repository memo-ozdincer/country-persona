# Coordinate three workshop roles on the Mali docket

Three fictional drafting and technical desks each choose one value
in their assigned field. A public package requires all three roles'
compatibility. A narrow sign about package A reveals only the
addressed desk's binary condition under the workshop rule. An
impasse can be certain while a condition is still unknown.
The historical record preserves two separate failed drafts
and the distinct reasons for failure.
[Official Council meeting](https://digitallibrary.un.org/record/4020239/files/S_PV.9408-EN.pdf) ·
[UN index of both outcomes](https://www.un.org/sites/un2.un.org/files/webform/s78.pdf) ·
[Dataset linkage](../../../crossbench/mali/references.json) · [Workshop contract](case.json)

The learned planner fits 11,178 action values on 46 synthetic
menus. It excludes the 24 menus equivalent to the held menu
under field permutations and value flips. It sees only the
public state, channel rates and question budget when deployed.
The exact comparator sees the same public information and
enumerates all delivery and requirement branches. Each table
cell is expected correct-decision rate and normalized net across
all eight fictional worlds. Net subtracts modeled question costs
from a documentary proxy for decision and mandate attribution.
[Protocol](protocol.md) · [Weights and all three budgets](experiment.json)

| Delivery by role, three-question cap | Fixed order | One-step greedy | Learned router | Exact public planner |
| --- | ---: | ---: | ---: | ---: |
| 0.90 / 0.90 / 0.90 | 0.790 / 0.553 | 0 / 0 | 0.851 / 0.602 | 0.851 / 0.602 |
| 0.90 / 0.80 / 0.35 | 0.423 / 0.164 | 0 / 0 | 0.327 / 0.128 | 0.490 / 0.221 |
| 0.35 / 0.93 / 0.72 | 0.316 / 0.075 | 0 / 0 | 0.483 / 0.209 | 0.483 / 0.210 |

With two questions and all rates at 0.90, the learned and exact
planners have a 0.405 expected correct-decision rate. The
one-step policy never starts because no single reply resolves
the initial state. The main learned failure occurs with the
weak technical desk, where the tree addresses that desk first
at both two and three turns. The exact planner starts with the
Russian drafting desk and the fixed control starts with France.
The learned policy also falls below silence after costs under
the two-question cap in that profile.

These are modeled delivery histories on an exposed historical
family and a new workshop structure. This supplements the
frozen benchmark. It does not change the public release's
case roster or its score definitions. The first CPU attempt
used the wrong relative source path. The fixed script hashes
both the actual historical packet and the existing linkage audit.

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 experiment.py | cmp - experiment.json
```

[Live replies and scored records](live/README.md) follow the learned route
to a 70-point agreement after three admitted replies and a 56-point
impasse after two. [Delivery-branch rollout](routing-rollout/README.md)
repairs the modeled low-delivery error and compares learned, greedy and
fixed continuations with exact planning.

[Shared outcome training](team-return/README.md) learns optional replies
and routing from sampled returns. The backward fit improves the same
chair's net by withholding unhelpful replies and recovers from the first
joint policy-gradient run's collapse to silence.
