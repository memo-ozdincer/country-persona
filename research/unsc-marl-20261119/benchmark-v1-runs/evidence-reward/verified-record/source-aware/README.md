# Account for source availability when deciding whether to ask

Removing the Cyprus vote source reduces a proved decision's released
record from 70 to 42. The former learned team cannot see this drop.
The new fit gives both chair and delegates two public values, the
score for a certified impasse and the score when all roles are
documented. These values are derived from available source fields and
the rubric. The training fit uses sampled returns on 46 synthetic
menus, excluding the shared Mali and Cyprus shape and all three
evaluation value pairs. The compact reward matches the frozen
documentary scorer on all 192 compatible private-world and public-state
pairs across the three source packets.

| Cyprus vote withheld | Questions | Former net | Source-aware net | Public selection net | Exact net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.90 / 0.90 / 0.90 | 2 | 0.0495 | 0.0570 | 0.0570 | 0.0570 |
| 0.90 / 0.90 / 0.90 | 3 | 0.1781 | 0.2001 | 0.2001 | 0.2416 |
| 0.90 / 0.80 / 0.35 | 2 | −0.0960 | −0.0180 | 0 | 0 |
| 0.90 / 0.80 / 0.35 | 3 | −0.0377 | 0 | 0 | 0.0159 |
| 0.35 / 0.93 / 0.72 | 2 | −0.0526 | 0 | 0 | 0 |
| 0.35 / 0.93 / 0.72 | 3 | −0.0187 | 0.0120 | 0.0120 | 0.0120 |

Net is expected released score divided by 70, minus the modeled
query and reply fees. The new pair improves all six vote-withheld
rows. It wins four of six full Cyprus rows and one of six Mali rows,
with losses in the remaining rows. At equal rates and two queries it
chooses a less useful opening and halves expected released points on
both full packets. Swapping only the chair captures much of the
gain in asymmetric Cyprus, while swapping only the responder can
reduce net when paired with the earlier chair. These are fixed-policy
cross-play controls. [Fit protocol](protocol.md) · [Weights, exact bounds and scores](results.json)

The separate public selection step evaluates each frozen pair under
the supplied rates and chooses the highest forecast net among the
pairs and silence. It recovers the residual loss in the withheld
two-question condition with a weak third desk, and preserves the
earlier pair on five of six Mali rows. Dominance over the selectable
pairs under a correct law follows from the construction. The exact
planner remains ahead in some cases by using choices unavailable
from those two pairs.

When actual delivery weakens while policies and selection keep the
old rates, the selected policy loses to silence in 13 of 18 stress
conditions. The worst net is −0.1379. This is a remaining deployment
limitation. These experiments use modeled delivery on two exposed
dockets, fixed source contracts and typed signs. There are no new
language model calls or parameter updates to Qwen. [Selection protocol](chooser-protocol.md) ·
[Saved-weight replay and shifted rates](chooser-results.json)

Run from this directory with the project Python and NumPy.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 source_aware.py | cmp - results.json
python3 chooser.py | cmp - chooser-results.json
```

[Delivery inference and selective probes](infer-delivery/README.md)
update the public rate belief from ordinary workshops. A separate
cautious decision rule reduces degraded-channel losses while giving
up some stable-channel opportunities.
