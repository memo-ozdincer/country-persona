# Test routing transfer under inventory and review shifts

The original interval selector loses most comparisons in the wider
suite. The matrix covers four exposed UN
dockets, eight previously held dense score banks and eight previously
held sparse score banks. It uses three unseen mixtures of inventory
laws, two conditions for whether the router knows the mixture, and
three review offsets. The 360 modeled conditions reuse 20 distinct
banks.

| Candidate set and selector | Wins | Losses | Mean net margin | Below silence on documentary points |
| --- | ---: | ---: | ---: | ---: |
| Original heads, point estimate | 62 | 240 | −0.0760 | 73 |
| Original heads, interval | 58 | 258 | −0.0731 | 65 |
| Forecast-trained replacement, point estimate | 55 | 246 | −0.0802 | 76 |
| Forecast-trained replacement, interval | 54 | 260 | −0.0800 | 68 |

The net comparison gives fixed targeting and silence the true score
bank and inventory mixture. The original interval method slightly
improves mean net and incurs more losses than the point estimate. Its
worst margin is also lower, at −1.6312 versus −1.3719. The underlying
reward control finds a positive gain available to exact adaptive
routing in 327 of 360 conditions.

## Fit with the grades the heads will actually observe

The replacement jointly optimizes eight scalar head weights on the
same 144 synthetic banks used for the earlier sparse fit, with no
held score bank in the 120-update fit. It computes actor features
from incomplete and sometimes noisy grades. The true bank supplies
the synthetic team reward. Training reward rises from 11.6882 to
12.3629 before opening costs. The soft training query rate rises
from 63.4% to 99.95%. Replacing the dense heads worsens held results
under both selectors. The sparse and scripted options stay available.
The fit ran on CPU and kept the Qwen checkpoint frozen.
[Held matrix protocol](protocol.md) · [Original results](results.json) ·
[Training design](training-protocol.md) · [Weights and held results](fitted.json)

## Separate the review budget from the learned heads

Use the 120 rows with zero simulated grading error. On the 48 dense
synthetic rows, exact planning with one reviewed pair wins 31 and
loses 17 against fully informed fixed targeting. Reviewing all three
pairs and predicting the triple gives 48 wins. The two additive UN
dockets gain little or nothing from pair review. The cross-role
historical pairs help mainly when the advertised inventory is shifted.
The seven-grade exact result spends two more review observations
per case than the five-grade result, with review cost outside net.

Under the correct mixture, the mixed learned selector's dense-bank
mean margin improves from −0.0427 at five grades to +0.0034 at seven,
versus +0.0670 for exact planning at seven. At eight grades it appears
to lose six dense rows under the unrestricted fixed comparison. Those
six losses become ties when the reference is limited to the fixed and
silent net-optimal options that also preserve the mixed selector's
silence-level documentary floor. Each target keeps its unrestricted best reply in this filter. The supplied prior still matters.
Seven full-grade dense losses persist under the shifted prior against
the filtered reference. [Exact planner](information.json) ·
[Learned policies](learned-information.json) · [Matched floor](quality-alignment.json)

This replay uses modeled delivery, synthetic and previously exposed
score banks, same-assistant historical marks and frozen routing priors.
It establishes a broader failure of one-pair calibration and a measured
path for using more grade information. End-to-end generalization remains unmeasured.

Run with the parent Python environment and import paths.

```bash
set -o pipefail
python3 shift_audit.py | cmp - results.json
python3 fit_forecast.py | cmp - fitted.json
python3 information_frontier.py | cmp - information.json
python3 learned_frontier.py | cmp - learned-information.json
python3 quality_alignment.py | cmp - quality-alignment.json
```

An initial invocation targeted the parent derived result file rather
than this folder. The parent file was rebuilt from its sealed grades,
and its prior sensitivity report still compares byte for byte. The
native traces and grade inputs were preserved.

[Model-based team policy improvement](policy/README.md) compares
coordinated routing to fixed targeting at the same review and prior
information. It also replays the action tables through the source-bound
record dispatcher.
