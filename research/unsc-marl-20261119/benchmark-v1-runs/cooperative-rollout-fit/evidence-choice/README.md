# Learn role-local evidence selection from shared return

The structured policy selects documentary passages for all three desks.
Each scores its local choices with the same three fitted coefficients.
One coefficient weights local coverage, and two weight estimates of
joint coverage under different partner forecasts. The optimizer
enumerates the joint choices and updates all three roles from the same
documentary return. It uses no target action labels. The actor receives
only its own features, with no partner notes or selected actions.
[Protocol](protocol.md) · [Locked inputs](plan.json)

The initial CPU fit uses 96 synthetic scenarios and 150 exact-gradient
updates. Expected training return rises from 25.58 to 37.79. On 48
separate synthetic scenarios the deterministic learned policy averages
37.08, compared with 29.63 for local-only selection, 37.00 for the
uniform-partner rule and 37.13 for the priority-forecast rule. The
joint oracle averages 37.42. A finite difference check confirms the
policy gradient against the exact objective. The run evaluates
260,928 joint selection returns including the final readout.

| Archived full-receipt result | Frozen language | Local coverage | Priority forecast | Fitted selector | Joint oracle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Resolution 2475, disability protection | 56 | 70 | 70 | 70 | 70 |
| Resolution 2422, residual tribunals | Unavailable at matched capacity | 57 | 57 | 58 | 58 |

The structured inputs include authored score and relation tags
from the existing rubrics. On Resolution 2475 the tags make the
missing France choice clear to every score-aware rule. On Resolution
2422 the fitted Peru desk chooses the call for Council unity over the
cooperation passage. The Russia staffing passage unlocks a joint
criterion. Receipt of both makes that choice worth one point more
than the local alternative. The structured policies use stable IDs,
which makes reversal invariance a property of the interface. The
positional control falls from 70 to 42 on Resolution 2475 and from
57 to 43 on Resolution 2422 after reversal. A preparation check caught
the first adapter's incorrect assumption about the Tribunals weights.
[Shared-return results](results.json) · [Mapping repair](preparation.md)

## Account for delivery uncertainty

A second fit preserves the learner and adjusts the reward and
features for independent message delivery. The receiver advertises
each role's receipt probability before selection. A fixed control
tunes one coefficient on the same synthetic fitting scenarios. It
selects the ordinary priority forecast. A further rule, evaluated
after the fitted result, assumes partners choose compatible claims
when available. It uses the advertised pair stakes and probabilities.
[Delivery protocol](delivery-aware/protocol.md) · [Results](delivery-aware/results.json) ·
[Optimistic coordination control](delivery-aware/coordination-control.json)

| Policy on the 48 synthetic delivery scenarios | Mean return | Ties with joint oracle |
| --- | ---: | ---: |
| Original weights and full-receipt features | 19.5837 | 34 |
| Fixed priority forecast with delivery adjustment | 19.8307 | 43 |
| Original weights with delivery-adjusted features | 19.9463 | 43 |
| Fixed optimistic coordination rule | 19.9479 | 43 |
| Delivery-aware refit | 19.9536 | 44 |
| Joint oracle | 20.0101 | 48 |

Adapting the original features recovers most of the loss. Refitting
adds 0.0073 points over the original weights on the adjusted features.
There is one fitted seed with 48 synthetic evaluation cases.

On Resolution 2422 the full-receipt switch costs two points when
only Peru's change reaches the chair and adds three when Russia's
matching claim also arrives. With a common independent receipt
probability p, its expected gain is p × (3p − 2). The fitted
delivery-aware policy avoids the original losses at 0.35 and 0.55.
At 0.75 it stays with the local choice and leaves 0.1875 of expected
credit on the table. At 0.95 it switches, gaining 0.8075 over the
local rule. The optimistic control makes the oracle choice at all
four rates for both archived dockets. The replay checks 208 distinct
joint selection and receipt records through the archived score paths.
No model weights or natural-language claim extraction were fitted.

The test gives a concrete shared-return learner and a stronger simple
coordination baseline. The archived effects depend on authored
priorities and a modeled channel. The strongest archived results are
reproduced or exceeded by fixed controls. Evidence on unseen families
and real delivery remains open.

## Reproduce

Set up the Python variables from the [parent reproduction guide](../README.md#replay).
From this directory:

```bash
set -o pipefail
"$py" learn_choice.py plan | cmp plan.json -
"$py" learn_choice.py run | cmp results.json -
cd delivery-aware
"$py" loss_aware.py plan | cmp plan.json -
"$py" loss_aware.py run | cmp results.json -
"$py" coordination_control.py | cmp coordination-control.json -
```
