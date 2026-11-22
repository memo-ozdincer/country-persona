# Coordinate a shared Iraq and Syria workshop agenda

Each desk may send one authenticated mandate across two concurrent
dockets. The chair can publish only a decision that is acceptable in
every frozen workshop world consistent with the delivered cards. The
policies see their own card availability, public agenda priorities,
delivery rates and the availability prior. They do not see the other
desk's inventory. The game compares simultaneous reports, public
receipt feedback and public certificate feedback.

The environment checks the eight frozen workshop worlds against their
package fields and verifies the 256 combinations of agenda worlds and
receipt states. A first-desk card already warrants a decision in two
of four worlds per family. In those cases, a shorter term leaves a
package that also satisfies either second-desk mandate. A second-desk
card alone never warrants a decision, and both cards suffice in all
cases. These are exact completion checks against the v1.5 packet.

The experiment fits two local softmax heads from exact expected shared
return for 300 CPU updates per setting. Training uses one 36-setting
synthetic panel. The fitted policies are replayed on 48 held conditions
drawn from separate availability, priority and delivery settings.
The assumptions use uniform workshop worlds independent of inventory
and delivery. The public rate estimates are supplied. The payoff is
the priority-weighted warranted decision minus 0.06 per attempted
report. This is a workshop action diagnostic with simulated transport.
[Locked first protocol](protocol.md) · [Preparation corrections](preparation.md)

## Simultaneous and sequential reporting

| Policy | Simultaneous net | Sequential net |
| --- | ---: | ---: |
| Fitted heads, greedy | 0.299660 | 0.332564 |
| Fitted heads, sampled | 0.280229 | 0.317961 |
| Best shared docket order or single target | 0.303103 | 0.333387 |
| Local conditional expected value | 0.304095 | 0.333387 |
| Exact decentralized optimum | 0.308131 | 0.333387 |

On simultaneous reports, the joint fit beats the best shared priority
in one condition, ties 35 and loses 12. Its extra reports leave it
below the local conditional rule. Under receipt feedback the fixed
rule and exact optimizer tie on every condition. The greedy fit ties
the fixed rule on 43 of 48 conditions. Swapping the trained opener
for the fixed one recovers the full gap. Swapping the trained follower
preserves the learned team's return. These comparisons hold the
certificate checker fixed.
[Fit, control actions and every dispatch](results.json)

## Announce that the first report already warrants a decision

A dependent fit shares the chair's proof status with the second desk.
The original network still sees the receipt under either proof status
in the paired no-proof control.

| Policy | Net | Weighted decisions | Attempted reports | Redundant second reports |
| --- | ---: | ---: | ---: | ---: |
| Frozen receipt-only fit | 0.332564 | 0.392022 | 0.990968 | 0.143865 |
| Proof-aware fitted heads, greedy | 0.341196 | 0.392022 | 0.847103 | 0 |
| Proof-aware fitted heads, sampled | 0.325588 | 0.379680 | 0.901531 | 0.061332 |
| Proof-aware fixed policy and exact optimum | 0.342081 | 0.392969 | 0.848131 | 0 |

The proof-aware greedy fit saves 0.143865 attempts and gains 0.008632
net per agenda with identical weighted decision coverage. The
certificate indicates when another card can help. The fitted follower
acts on that signal. A fixed proof-aware follower gives exactly the
same result with the learned opener. Replacing the learned opener
closes the remaining 0.000885-point gap. This is a measured benefit of a
public coordination signal that a learned policy can use. It gives
no advantage over a fixed policy with that same signal.

The experiment trains finite-action policies on a new simulated
communications constraint applied to exposed workshops. It does not
assess new language outputs, final-record scores, or transfer to
unseen UN families.
[Follow-up protocol](proof-feedback-protocol.md) · [Proof-status replays and swaps](proof-feedback.json)

## Verify

Use Python with NumPy and PyTorch. From this directory:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python experiment.py | cmp results.json -
python proof_feedback.py | cmp proof-feedback.json -
```
