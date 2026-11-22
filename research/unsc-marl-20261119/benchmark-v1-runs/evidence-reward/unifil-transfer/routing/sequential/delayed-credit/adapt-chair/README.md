# Adapt the chair and responder to delegate availability

The chair now takes the last-step availability profile into account
when choosing both questions. It evaluates the possible requirements
consistent with the public signs and predicts whether the role will
send. The first responder uses the prior fitted weights. The
record-aware exact control uses the same public prior and declared
availability. It has exact modeled gains for each delivered sign.
A missing reply leaves the public evidence alone. At the 80%
delivery comparisons none of the evaluated planners skipped the
first slot and then used the last slot.
[Availability-aware policy](adaptive.py) · [Protocol](protocol.md) · [Replay](adaptive.json)

| Last-step availability at 80% delivery | Frozen chair, net | Adapted learned team, net | Adapted exact control, net | Frozen chair questions to a known unavailable role |
| --- | ---: | ---: | ---: | ---: |
| Both delegates available | 316.074 | 314.834 | 315.548 | 0 |
| Desk One absent | 260.714 | 292.376 | 295.074 | 119 |
| Desk Two absent | 239.160 | 289.827 | 289.351 | 131 |
| Both available 25% of the time | 207.278 | 211.991 | 211.649 | 0 |

Both adapted policies eliminate questions to definitely absent roles.
The learned team earns 50.667 more net with Desk Two absent.
It loses 1.240 net when both are available, where the altered
ranking sends more questions. The exact control has the same
public information. Differences in actual returns can favour
either policy because the three evaluation worlds do not follow
the uniform public prior exactly.

At 8% delivery the adapted learned team still loses relative
to silence in every availability scenario. Its downstream value
overestimate survives removal of unavailable routes. The exact
adapted control is positive in all four scenarios. This run
changes how the fitted policies are used. It adds no training
or Qwen calls.

## Estimate availability from paid reply acknowledgments

Before running the learned team, collect acknowledgments that do
not depend on the local mandate. Update a uniform prior over four
availability profiles using exact receipt likelihoods. Deploy
with posterior mean availability. The link success rate is supplied
as 0.80 throughout. Fees accrue even if an acknowledgment is lost.
Each measured return is an expected mean per dialogue, before
the one-time cost of learning about that partner.

| Actual availability | No probes | One probe per role | Two per role | First profitable dialogue count, one / two |
| --- | ---: | ---: | ---: | ---: |
| Both available | 0.4089 | 0.4065 | 0.4083 | — / — |
| Desk One absent | 0.3389 | 0.3626 | 0.3770 | 5 / 7 |
| Desk Two absent | 0.3098 | 0.3612 | 0.3723 | 3 / 4 |
| Both rarely available | 0.2821 | 0.2785 | 0.2794 | — / — |
| Outside prior support, 0.40 and 0.95 | 0.3620 | 0.3631 | 0.3650 | 113 / 85 |

The absence cases benefit if availability persists over the shown
number of dialogues. Probing has negative expected value on the
available and rarely available profiles, even before its cost.
The out-of-prior profile benefits only over a much longer horizon.
These are fixed probing budgets with exact simulation of receipt
counts and 768 evaluation openings per profile. Live acknowledgments,
adaptive probe stopping, and joint inference of link loss and
delegate readiness remain unmeasured.
[Receipt-learning protocol](availability-learning-protocol.md) · [Policies and all receipt branches](availability-learning.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 adaptive.py | cmp - adaptive.json
python3 availability_learning.py | cmp - availability-learning.json
```
