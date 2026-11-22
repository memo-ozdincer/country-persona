# Estimate delivery from public replies and decide when to keep asking

The earlier policy selection used announced delivery rates. This
experiment updates a belief about stable but unknown rates over 24
workshops with new private requirements each time. The two fitted
teams keep their original chair and reply heads. The selector sees the
public menu, selected policy and reply trace. It updates across
workshops. A public silence event leaves two possibilities, intentional
withholding and transmission loss. Under a learned gate that sends for
one of two equally likely hidden bits, the probability of a miss is
(1-r/2), where (r) is the delivery rate. A compulsory send has miss
probability (1-r). A policy that always withholds produces no rate
evidence. The code checks these three cases and verifies normalization
for 283 terminal public trace patterns.

The campaigns reuse the prior source-checked renderer, rubrics, fees
and frozen pair of candidate teams. A hindsight reference selects
among those pairs and silence with the true delivery law. It cannot
see the actual private requirements or receipt draws. All strategies
share the same 512 simulated campaigns per condition. The results
measure modeled operating behavior with stipulated stable channels
and known reply policies. No new text model calls or fits occur.
[Protocol](protocol.md) · [Per-workshop results and paired standard errors](results.json)

## Delivery shifts and the cost of probing

Equal-condition means below are normalized reward after fees over
24 workshops. The degraded group contains 18 conditions across
three missing-source and docket settings. The stable group contains
six. They are descriptive summaries over the fixed test matrix.

| Selector | Mean net, degraded | Negative degraded conditions | Mean net, stable |
| --- | ---: | ---: | ---: |
| Nominal rates | −1.011 | 13 / 18 | 6.386 |
| Prior, no updates | −1.043 | 13 / 18 | 6.348 |
| Naive miss update | 0.072 | 12 / 18 | 5.743 |
| Reply-aware update | −0.078 | 13 / 18 | 6.293 |
| Three compulsory pings | −0.285 | 16 / 18 | 5.983 |
| Reply-aware update with caution | 0.161 | 7 / 18 | 5.301 |
| Caution with selective pings | 0.100 | 10 / 18 | 5.883 |

The correct update reduces the losses from the nominal selector but
is slower to stop than naive updating in many degraded cells. Naive
updating also sacrifices stable-channel reward. For example, with a
complete Cyprus packet, two questions and stable 90% rates, the
correct update earns 5.151 over the campaign and the naive update
earns 4.273. With all three physical rates at 45%, those two methods
earn −1.199 and −0.395 respectively. A more accurate account of why
a reply is absent does not alone fix the exploration cost.

Requiring 80% posterior support for positive net cuts the number of
negative degraded conditions. It also stays silent on two stable
conditions. Selective pings recover some of that loss. For stable
Mali with two questions, caution alone stays silent, and selective
probing earns 2.265, with 1.150 probes per campaign on average. The
unrestricted reply-aware update earns 2.974 there. For stable
vote-withheld Cyprus at two questions, neither cautious method starts
communication, despite positive hindsight candidate value. When
degraded, probes beat caution alone in two of 18 conditions. Paying
to probe all three roles yields a lower mean than the unprobed
reply-aware selector in every tested condition.
[Selective probe protocol](selective-probe-protocol.md) ·
[Paired results](selective-probe-results.json)

These experiments quantify the trade between saving message cost and
losing opportunities to certify a decision. The candidate policies
stay fixed at their nominal-rate settings. The finite prior and stable
unknown rate assumption are supplied. There is no test here of
changing rates inside a campaign or of an unfamiliar reply policy.

Replay from this directory with the project Python and NumPy.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 infer.py | cmp - results.json
python3 selective_probe.py | cmp - selective-probe-results.json
```
