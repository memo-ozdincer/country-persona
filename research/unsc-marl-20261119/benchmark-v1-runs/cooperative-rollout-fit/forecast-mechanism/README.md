# Where the learned grade correction helps UN routing

With the exact adaptive optimizer held fixed, the learned correction
helps primarily through the reported **pair grade**. Moving that grade
halfway toward the additive estimate from the two singleton scores
matches or exceeds the learned pair correction's mean net gain on all
three aggregate comparisons. Both methods leave the other observed
grades and the inferred full-receipt grade unchanged.
[Protocol](protocol.md) · [Results and branch replays](results.json)

| Grade change | Historical archive, 90 conditions | Scoped writer, 18 conditions | Verbatim writer, 18 conditions |
| --- | ---: | ---: | ---: |
| Learned pair | +0.0347 | +0.0701 | −0.0011 |
| Learned full receipt | −0.0049 | +0.0001 | 0.0000 |
| Both learned | +0.0344 | +0.0686 | −0.0011 |
| Upward-only learned pair | 0.0000 | +0.0616 | −0.0011 |
| Halfway toward additive pair estimate | +0.0396 | +0.0705 | 0.0000 |
| Constant +3.5 to pair | −0.0070 | +0.0328 | −0.0071 |

Entries are mean net points relative to the unmodified forecast under
the same exact planner. Both learned and additive pair corrections
lower the historical count below informed silence from 18 to 10 and
the scoped count from two to zero. The verbatim writer has zero
below-silence conditions in every variant.

The correction acts in different directions. The historical mean gain
comes from the deliberately overgraded rows, where learned and additive
corrections gain +0.1229 and +0.1238. Both slightly lose on the historical
undergraded rows. On the scoped bank, undergrading is the largest
opportunity. The two rules both average +0.1859 across the six undergraded rows, while the mean gain on exactly graded rows is −0.0009 for
learning and zero for additive shrinkage. Thus the previous evidence
of benefits under undergrading describes the scoped case. The direction
depends on how the noisy pair compares with the score supported by the
singleton records.

All variants share legal actions, openings, expected-return optimizer
and information. The learned strength stays frozen at its value from
synthetic validation. There are 882 independent exact branch replays.
The two writer variants share Resolution 2686. The reported net scores
use modeled receipt inventories, delivery and communication costs,
with historical case grades from exposed archival runs.

## Hold the robust planner fixed

Both corrections improve the robust planner on the Resolution 2686
scoped-rewrite bank. Each adapted team beats its own same-forecast
fixed policy in 18 of 18 simulations. The learned comparison has a
larger margin against its own fixed comparator because the additive
correction also improves the fixed policy. Against the common
uncorrected team, additive has slightly higher mean net. Both bring
the two below-silence results to zero.

| Bank and pair correction | Wins / losses / ties against uncorrected team | Mean gain against uncorrected team | Mean gain against same-forecast fixed |
| --- | --- | ---: | ---: |
| Scoped, learned | 11 / 0 / 7 | +0.0799 | +0.1276 |
| Scoped, half additive | 10 / 0 / 8 | +0.0844 | +0.1008 |
| Verbatim, learned | 2 / 5 / 11 | −0.00008 | +0.1133 |
| Verbatim, half additive | 2 / 0 / 16 | +0.0014 | +0.1121 |

The robust run reproduces the original archived results before applying
the two corrections. It checks all 216 policy dispatches, including 14
randomized policies. A separate test reconstructs those randomized
outcomes as weighted deterministic tables. The largest net, release,
cost or query discrepancy is below 4 × 10⁻¹⁴.
[Follow-up protocol](robust-protocol.md) · [Scoped replay](robust-scoped.json) ·
[Verbatim replay](robust-verbatim.json) · [Mixture audit](mixture-audit.json)

The current evidence supports correcting an unstable pair grade.
The simpler additive control reproduces the learned benefit in the
matched comparisons. A learned advantage would need to show up on
records whose true pair coverage departs from the additive estimate,
under a source-grounded evaluation locked before generation.
These experiments reuse exposed records and a simulated channel.

## Reproduce

Use the Aurora environment and `replay` helper in the
[parent instructions](../writer-transfer/README.md#reproduce). Run in
this directory with Bash pipe failure enabled.

```bash
set -o pipefail
replay forecast_mechanism.py plan | cmp plan.json -
replay forecast_mechanism.py run | cmp results.json -
replay robust_followup.py plan | cmp robust-plan.json -
replay robust_followup.py scoped | cmp robust-scoped.json -
replay robust_followup.py verbatim | cmp robust-verbatim.json -
replay audit_mixtures.py | cmp mixture-audit.json -
```
