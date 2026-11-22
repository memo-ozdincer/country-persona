# Learn whether to send a reply whose value comes on the next turn

The trained UNIFIL chair is frozen. Compare mandatory first replies,
an immediate-value gate, and optional first replies trained on the
final state after the next question. Every arm uses the same exact
local send gate on the last turn. For each synthetic first query, the
trainer replays sending and passing with identical final-turn policy
and delivery assumptions. It fits the difference in team return from
the two counterfactual outcomes. The first responder observes its
own verified requirement and public evidence. Its continuation
feature conditions on the local requirement and averages over the
peer's remaining public possibilities.
[Protocol](protocol.md) · [Fitted margins and held paths](delayed.json)

| UNIFIL first responder at 80% delivery | First replies | First replies with no immediate gain | Expected questions | Expected score gain | Normalized net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mandatory send | 607 | 211 | 961.0 | 385.472 | 314.489 |
| Exact immediate-value gate | 396 | 0 | 901.0 | 305.600 | 248.434 |
| Fitted two-turn credit | 548 | 152 | 979.4 | 385.728 | 316.074 |
| Exact public two-turn credit | 548 | 152 | 979.4 | 385.728 | 316.074 |

The fit uses 11,188 counterfactual comparisons from the sixteen
original synthetic worlds, across four modeled delivery rates.
At 80% on UNIFIL it keeps all 394.56 expected proofs of the
mandatory-first control. It saves 59 first replies and asks 18.4
more expected questions after the changed observations. Total
communication cost falls by 1.329. It sends in all three openings
from the previous live witnesses, where the immediate-value
responder passes. There are no new Qwen calls in this experiment.

At 8% delivery all four responder policies earn −0.296 net. The
frozen chair still asks in marginal states where its proxy
overvalues the record. The optional first reply does not resolve
that upstream calibration error. The initial training run hit a
UNIFIL-specific field-name lookup on a synthetic menu. The fixed
training replay enumerates the fields of each synthetic menu and
leaves the original routing code and held case unchanged.

## Change the last delegate without refitting

Freeze the first responder weights and the chair. After its last request, availability
can differ by delegate. Test giving the first responder the declared
availability, while keeping the chair frozen. All entries are
normalized net totals at 80% channel delivery.

| Last-step availability | Mandatory first reply | Fitted, assumes both available | Fitted, uses declared availability | Exact public credit |
| --- | ---: | ---: | ---: | ---: |
| Both available | 314.489 | 316.074 | 316.074 | 316.074 |
| Desk One unavailable | 254.168 | 255.625 | 260.714 | 260.714 |
| Desk Two unavailable | 229.916 | 231.373 | 239.160 | 239.230 |
| Both available 25% of the time | 205.819 | 207.212 | 207.278 | 207.190 |

With Desk Two unavailable, the availability input changes 103
first replies and raises net by 7.787. A missing reply can remove
the value of the previous turn even when the initial sign was
truthful. The remaining cost includes questions the frozen chair
still directs to an unavailable role. The exact reference integrates
the public prior, and the reported outcome is measured on the three
sampled worlds. This explains why small differences can favour
either arm on that cohort.
[Partner protocol](crossplay-protocol.md) · [Cross-play results](crossplay.json)

This is counterfactual training and replay over a prescribed
public belief model, known fees, and one exposed event family.
Declared availability is supplied to the policy. Inferring it
during dialogue and adapting the chair remain unmeasured.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 delayed.py | cmp - delayed.json
python3 crossplay.py | cmp - crossplay.json
```
