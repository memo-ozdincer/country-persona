# Three-delegate certified package workshop

Three delegates each hold one private card drawn from four public possibilities. Each files one exact grade. After delivery losses, the chair may request one more grade. A zero excludes that package. The chair releases a recommendation only if all complete worlds compatible with the receipts share a best package by lower grade and then total. It records impasse only when every compatible world excludes all packages. The certificate uses admitted grade values, with no inference from the act of choosing a slot. [Locked protocol](protocol.md) · [Environment and policy fit](../warrant_three.py)

The three opening policies learn together for 96 exact policy-gradient updates under a shared reward. The chair chooses the request with the highest expected certified return given the admitted openings. Train on 16 domains and evaluate the following 12 generated domains under two priors. Compare with public lookahead, constant package slots and coordinate search that improves one role's four-type table at a time. Coordinate search starts from both the initial and best constant designs. The full-information upper bound allows the coordinator to select disclosures and questions using the world, subject to the same evidence rule.

## Results

| Mean held net | Uniform inventories | Correlated inventories |
| --- | ---: | ---: |
| Random opening slots | 0.613149 | 0.628544 |
| Best constant slots | 0.821230 | 0.839723 |
| Initial public lookahead | 0.880681 | 0.886276 |
| Fitted disclosures | 0.880681 | 0.886022 |
| Coordinate search | 0.882129 | 0.888759 |
| Full-information upper bound | 0.907980 | 0.907180 |

The fit ties lookahead in 22 of 24 conditions, wins one and loses one. The coordinate search ties the fit in 18 conditions and beats it in six. Disabling the follow-up while keeping the fitted opening drops mean net by 0.147896 and 0.148965. Communication after observing receipts adds useful evidence in this environment. The stronger local opening baseline captures the same net gain. The audit independently reconstructs the permissible decisions and verifies the fitted results on all 512 opening branches per condition. [Held policy tables and outcomes](results.json) · [Receipt audit](audit.json)

The stochastic training objective rises from 0.807196 to 0.890041 by update 96. A follow-up calibration uses only the original training domains to choose the sharpness of the initial policy. The original stochastic scale scores 0.807196 on training. The same action rule with deterministic maximum scores 0.895604, slightly above the fitted stochastic policy's 0.890084. On held domains, the learned stochastic policy earns 0.874890, up from 0.787782 at the original initial scale. Deterministic lookahead earns 0.883478. Entropy of the opening choices falls from 0.942 to 0.453 nats under the fit. Together with the near-tie on discrete choices, this indicates that improved training returns can mostly reflect making existing choices more decisive. [Training-only scale calibration](temperature.json)

The experiment covers three synthetic agents, known public domains and exact authorized evidence. The measured coordination gain comes from an evidence-conditioned request. Outcome quality in natural-language diplomatic deliberation remains unmeasured in this setup.

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python warrant_three.py
OPENBLAS_NUM_THREADS=1 python warrant_three_audit.py warrant-three-evidence/results.json
OPENBLAS_NUM_THREADS=1 python warrant_three_temperature.py warrant-three-evidence/results.json
```
