# Adapt the chair to unfamiliar workshop partners

The chair chooses one optional follow-up after three role-local disclosures. Keep the original losses, message fees and rule for publishing a warranted decision. The chair may infer which grade to request from its partner model. The certificate considers every complete world compatible with the admitted grades. The known-partner oracle sees the true disclosure tables, with the same private-information restriction as the other chairs. [Locked protocol](protocol.md) · [Requester headroom](headroom.json)

The first comparison freezes the previously fitted opening policies, three single-role conventions and two unfamiliar teams. The mixed team combines familiar conventions that were previously modeled as homogeneous. The coordinate-search team's tables lie outside that convention model. The chair learns from up to 16 earlier ordinary opening ledgers without issued probes, private card identities or reward labels. Compare a three-style homogeneous model, the 27 combinations of role-specific styles and a no-history planner. The follow-up estimates per-role categorical action likelihoods with EM. Finally, a single chair weighs the two stronger models by their predictions of four reserved receipt histories. [Role model](../warrant_requester_adapt.py) · [Flexible model](em-protocol.md) · [Unified receiver protocol](blend-protocol.md)

## Results

| Opening team | Grade-only chair | Role-factored, zero histories | Role-factored, 16 histories | Unified receiver, 16 histories | Known-partner ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fitted | 0.879945 | 0.882779 | 0.883350 | 0.883318 | 0.883352 |
| Highest grade | 0.581129 | 0.592556 | 0.593807 | 0.593742 | 0.593815 |
| Veto first | 0.684689 | 0.686860 | 0.694089 | 0.693958 | 0.694197 |
| Mixed | 0.719475 | 0.723555 | 0.728372 | 0.728260 | 0.728404 |
| Coordinate search | 0.879104 | 0.881717 | 0.882561 | 0.884670 | 0.885444 |

The chair that assumes a fitted opening team scores 0.523282 against mixed partners and 0.819804 against coordinate search. Conditioning on the grade reports without assuming a sender convention already prevents much of that loss. Factorizing conventions by role provides additional value before learning. With 16 histories the factored model beats the grade-only chair in 18 of 24 mixed conditions and ties in six. The role-specific model falls 0.000032 short of the known-partner mean. The homogeneous posterior remains at 0.719442 on mixed teams, illustrating why a single profile for the whole team loses information. [Ordinary receipt adaptation](results.json)

The flexible model with a style prior scores 0.884736 on coordinate partners and 0.726641 on mixed partners. The unified receiver nearly keeps the better of the two choices in each setting. It gives the flexible model a mean weight of 0.812 on coordinate partners and 0.159 on mixed partners, based solely on reserved-receipt likelihood. It beats the grade-only chair in 12 coordinate and 18 mixed conditions and ties in the rest. It regresses in one veto-first condition and improves in 21. Both flexible comparisons use the same simulation panels after inspecting the first experiment. [Flexible estimates](em.json) · [Unified receiver and model weights](blend.json)

The experiment averages exact deployment branches after 32 sampled histories per domain, prior and team. No workshop reward enters the learner. Ordinary disclosures avoid extra probe costs but require up to 16 earlier workshops with the same opening team and a known inventory prior. These synthetic cross-play results validate receiver adaptation around the frozen local policies. Language-mediated disclosure, changes in partner behavior, and final-record quality remain untested by this replay.

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python warrant_requester_headroom.py
OPENBLAS_NUM_THREADS=1 python warrant_requester_adapt.py
OPENBLAS_NUM_THREADS=1 python warrant_requester_em.py
OPENBLAS_NUM_THREADS=1 python warrant_requester_blend.py
```
