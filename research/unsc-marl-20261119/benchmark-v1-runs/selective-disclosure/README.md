# Learn to send a grade only when it helps the recipient

The previous outer-space MARL team gained from seeing a peer's grade
and paid for that message on 99.67% of reserve episodes. Each desk
must report one authenticated grade to the chair. The first can also
send its chosen grade to the second desk before that desk chooses its
own report. The chair accepts only a package or impasse that survives
all legal completions of the received evidence. The simulated peer
opportunity is priced separately from delivery to the chair.

Use the original four development grids for fitting and four reserved
grids for evaluation. Those grids are variants of a simulated
outer-space compromise, selected for positive cooperation headroom by
an exact solver before the original fit. Reuse both learned delegate
policies and the verifier. First freeze the package choices and fit
only the paid send decision. Then allow the opener to jointly choose
the package and its send action while holding the recipient fixed.
Both use ridge fits to exact shared returns. Their baseline estimates
the continuation with uniform weights on the compatible worlds.
[Send-gate protocol](protocol.md) · [Opening protocol](joint-opener-protocol.md)

## Reserved outer-space grids

Means over the four reserved grids, with balanced worlds and the
original 0.03 message fee:

| Policy | Net return | Certified rate | Paid send rate |
| --- | ---: | ---: | ---: |
| Original learned team | 0.73805 | 76.80% | 99.67% |
| Fitted send gate, original package probabilities | 0.74769 | 76.00% | 41.05% |
| Joint opening value fit, frozen recipient | 0.75337 | 76.57% | 41.07% |
| Uniform forecast, same joint opening actions | 0.75337 | 76.57% | 41.07% |
| Exact opener, frozen recipient | 0.75337 | 76.57% | 41.07% |
| Exact independent team | 0.72321 | 72.32% | 0% |
| Exact peer-enabled team | 0.77304 | See per-grid receipts | Optimized |

The gate saves 0.586 attempted peer sends per world. Net improves
by 0.00963 while certification falls by about 0.80 percentage
points. Letting the opener change the grade as well recovers
most of that certification and adds 0.00569 net. The joint
opener beats the optimal independent team on every reserved grid.
The uniform forecast matches the fitted gate and opener at the
nominal fee. The same-recipient best response also matches both
stages under their respective legal action sets.

At 0.10 per send on the balanced reserve, the joint correction earns
0.72462 versus 0.72263 for the uniform forecast and reaches the
same-recipient optimum. Under a uniform-world deployment stress the
originally frozen correction trails that forecast at 0.015 and
0.10, and ties at the other two fees. These are model-based
estimates built from legal hypothetical private cards, public
payoff rules and the frozen partner policy. The fitted coefficients
learn a small adjustment to that forecast. Most of the nominal
gain comes from using the continuation forecast for both actions.

The exact transport replay uses the 12 archived model-written grade
statements, all of which previously passed grade binding. At the
nominal fee the language projection reproduces each policy's typed
score and certifies no unsupported decisions. The revised opening
reduces the estimated uncached model calls from 4.5974 to 4.1286 per
episode. The replay reuses a finite recorded vocabulary and adds
zero new generation or memo judgments.
[Gate results](selective.json) · [Joint opener and transport audit](joint-opener.json)

## Test two other source-linked grids

Apply the frozen opener and the same recipient to the existing Mali
and Myanmar-linked fictional grade grids. Average all six package
presentations. An exact solver allows either peer visibility or
independent reporting with equal evidence budgets.

| Grid | Original team | Joint fitted opener | Uniform forecast | Exact opener with same recipient | Both exact team optima |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mali | 0.53483 | 0.70547 | 0.70547 | 0.70547 | 0.73125 |
| Myanmar | 0.77879 | 0.79730 | 0.79730 | 0.79730 | 0.82350 |

The wider team can reach its full ceiling without sending a peer
message on these two grids. The frozen recipient best response still
sends in 50% and 40% of cases. Given that recipient, the fitted opener
reaches everything that can be obtained by revising the opening seat.
The lower score is a limitation of the frozen partner. These are
source-linked development grids with authored grades, not unseen UN
events or independently graded final records.
[Transfer protocol](family-transfer-protocol.md) · [All ordered replays](family-transfer.json)

## Reproduce

Use Python with NumPy, PyTorch and the existing workshop package in
this workspace:

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python selective.py | cmp selective.json -
python joint_opener.py | cmp joint-opener.json -
python family_transfer.py | cmp family-transfer.json -
```
