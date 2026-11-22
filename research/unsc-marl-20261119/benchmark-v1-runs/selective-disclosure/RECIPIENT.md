# Fit the recipient from outcome differences

The previous selective opener was already the best possible opener
with its old recipient fixed at the nominal fee. Freeze that opener.
The recipient still sees only its own grade card and a delivered peer
grade or silence. Its planner can enumerate possible first cards and
the opener's announced behavior. Only explicit received grades enter
the chair's exact warrant check. Inferring an unseen card's likelihood
never supplies an extra claim to the verifier.

First, regress a correction to the uniform-world continuation
forecast. Give the same policy-aware forecast to a fixed control.
Also compare a recipient that assumes uniform possible opening
reports and conditions on the observed grade alone. Then fit action
rankings from the signed counterfactual reward differences. The
second fit weights each choice pair by its actual gain and local
reach probability. Both fits use only the original four development
grids and keep all recipient action sets unchanged.
[Value-fit protocol](recipient-protocol.md) · [Action-ranking protocol](ranking-protocol.md)

## Results

All rows use the identical first decisions and the same 0.03 message
fee within each panel. The Mali and Myanmar rows average six package
orders. The four reserved outer-space grids were preselected for
communication headroom in the original study.

| Balanced worlds | Old recipient | Fixed forecast | Value fit | Action-rank fit | Exact recipient ceiling | Exact team ceiling |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Outer-space reserve | 0.753372 | 0.764411 | 0.758625 | 0.768750 | 0.768750 | 0.773036 |
| Mali | 0.705468 | 0.716250 | 0.716250 | 0.716250 | 0.716250 | 0.731250 |
| Myanmar | 0.797296 | 0.811500 | 0.803400 | 0.803400 | 0.811500 | 0.823500 |

The two fixed forecasts earn the same return in every panel. The
first fit reduces development error from 0.09403 to 0.07434 while
lowering held return relative to the fixed forecast on two balanced
panels. The ranking fit reaches the fixed-opener ceiling across the
balanced outer-space reserve. Its 0.004339 mean advantage over the
fixed forecast comes from grid 198, where it adds 0.01736. All other
reserve-grid scores tie. The original fixed-opener gap to the full
team optimum falls from about 0.01966 to 0.00429. The recipient change
uses the same number and size of typed messages.

On uniform worlds the same rank fit drops to 0.7500 on the reserve,
versus 0.7545 for the fixed forecast. The 0.0045 gap again comes
entirely from grid 198. The fitted Myanmar scores fall below fixed
under both world priors. The check that blocks a learned action
when the public forecast prices it at more than 0.02 below its own
best choice ties the fixed forecast on every panel. That check
prevents the losses and foregoes the balanced reserve gain.

These are exact decision-policy replays on simulated grade grids.
The 12 previously archived Qwen messages transport every tested
grade without changing certification in the reserved grids. This
adds no new language calls or final-record evaluations. The Mali
and Myanmar scenarios use prior public case menus and simulated
private grades. They are fit-excluded and previously exposed.
[All value fits, selected actions and receipt checks](recipient.json) · [Ranking result and override mass](ranking.json)

## Verify

Use the project Python environment with NumPy and PyTorch.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python recipient.py | cmp recipient.json -
python ranking.py | cmp ranking.json -
```
