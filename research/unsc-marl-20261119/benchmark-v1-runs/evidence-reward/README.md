# Reward evidence that supports the final workshop record

The previous signed-reply study found agreement proofs that left a
delegate's mandate ambiguous. This test replays the 44 fit-excluded
Iraq and Syria presentations with that documentary gap as a separate
endpoint. A record opportunity requires an explicit public decision
proof and an identifiable mandate for each role. The chair infers
candidates only from the public menu and delivered signs, under the
assumption of one requirement per role. An identifiable mandate
may still need to be described as inferred. This endpoint does not
score actual prose or turn an inference into a direct quote.

## One question leaves the gap open

The exact planner chose identical actions with or without the evidence
bonus. Granting it the option to ask either role for a full mandate
also left the policy unchanged. It made 28 requests for a sign and
stayed silent 16 times. At modeled delivery of 0.8, it yields 16.80
expected explicit proofs, of which 13.60 support both mandates.
In all four overlap presentations with ambiguous attribution, the
opening leaves both mandates ambiguous. A full reply from the original
recipient proves the decision and leaves the other role ambiguous.
A full reply from the other role identifies its condition and leaves
the explicit proof incomplete. The held full replies are reconstructed
from archived complete declarations, not observed in these exact
question contexts.
[One-question protocol](protocol.md) · [Exact policies and branches](exact.json)

## Fit the next question and reply together

Freeze the signed first stage. Once a decision is proved, a new chair
head can ask either role for its mandate or stay silent. A new
responder head can send a full disclosure or pass. Train the two small
linear heads jointly on synthetic workshop paths by exact gradient
ascent on their common expected reward. Use local truth verification
and the archived role's complete declaration for held deliveries.
Both true mandates may be identifiable even when only one was stated
in full. The sender must accept the field recorded by its own card.

| Policy after the first stage | Expected proofs | Expected complete record opportunities | Extra questions | Mean net return |
| --- | ---: | ---: | ---: | ---: |
| Stay silent | 16.80 | 13.60 | 0 | 0.4982 |
| Always ask the original recipient | 16.80 | 13.60 | 16.80 | 0.4447 |
| Ask the ambiguous role | 16.80 | 16.16 | 3.20 | 0.5171 |
| Exact cost-aware policy | 16.80 | 16.16 | 3.20 | 0.5171 |
| Fitted chair and responder | 16.80 | 16.16 | 3.20 | 0.5171 |

The fit uses 120 CPU updates, 136 terminal training paths with total
reach weight 59.22, and zero updates to Qwen. The learned team reaches
the exact result under the original held conditions. The features
explicitly tell the heads whether the addressed role is ambiguous
and whether the other role is known. The result demonstrates
coordination inside that typed environment and gives no improvement
over the simple ambiguity rule.
[Joint fit protocol](followup-protocol.md) · [Weights, trace and per-case results](followup.json)

## Stress the delivery assumption

With the first-stage paths and trained weights frozen, lower only the
follow-up delivery rate. At 0.20 the team still spends 3.20 expected
extra questions and loses 0.128 total net reward relative to silence.
The exact policy stays silent. At 0.28 the learned team spends the
same budget for zero net gain. At 0.95 it matches the exact policy's
1.072 gain. The synthetic delivery rates are all above the 0.28
break-even point. Reliable learned coordination under costly,
unreliable delivery remains unverified.
[Reliability protocol](reliability-protocol.md) · [Stress outcomes](reliability.json)

The initial fit replay required a correction to avoid looking up a
private held realization for a synthetic row. The fixed implementation
uses its public distribution over compatible branches during fitting.
There are no new model calls. Both event families have prior project
exposure, and multiple presentations share the same private mandates.

## Verify

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 environment.py | cmp - exact.json
python3 followup.py | cmp - followup.json
python3 reliability.py | cmp - reliability.json
```

## Recover the cost threshold with counterfactual values

Adding low and high delivery cases to the original joint optimizer
improves its synthetic training objective but leaves all nine held
greedy comparisons unchanged. It still asks at delivery rates 0.12,
0.20 and 0.275, losing 0.256, 0.128 and 0.008 total net respectively
relative to silence. At 0.28 it uses 3.20 expected questions at zero
net gain. The exact policy saves that budget. At each higher rate
the original and broadened policies match the exact baseline.
[Delivery calibration protocol](calibration-protocol.md) · [Fit trace and stress results](calibration.json)

Fitting the send-versus-pass and ask-with-answer-versus-silence
values separately recovers the underlying cost convention. The
responder estimates 0.5 times successful completion probability
minus the send cost. The chair estimates the same amount minus both
costs. The policy asks only when both fitted values are positive.
The two linear heads use 5,712 weighted synthetic rows each and reach
zero action error and regret against the exact policy across all 36
delivery and cost conditions. Nine conditions use the original fees
and 27 use fees excluded from fitting. All probes preserve the
first-stage decision score.

The value fit uses counterfactual supervision from the synthetic
transition payoffs, with a visible feature indicating whether an
answer can identify both mandates. This differs from the original
joint expected-reward fit. It establishes calibration with a supplied
delivery probability and known fee schedule. Learning both payoffs
from live interactions and improving on the exact rule are untested.
[Value-fit protocol](value-protocol.md) · [Policy and complete cost grid](value-fit.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 calibrate.py | cmp - calibration.json
python3 value_fit.py | cmp - value-fit.json
```
