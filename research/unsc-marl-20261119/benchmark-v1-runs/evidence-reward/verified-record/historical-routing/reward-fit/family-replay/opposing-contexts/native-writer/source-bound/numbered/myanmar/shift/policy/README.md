# Improve the communicating team directly under calibrated rewards

The team policy begins at an optimized fixed request or silence.
It searches for a better chair action at a reachable receipt mask
and recomputes the responder's best action at its own observation
boundary. This is model-based multi-agent policy improvement. The
language model stays frozen.

On the 48 dense clean-review rows, the one-state search beats the
fully informed fixed reference in 44 with seven grades and in all
48 with eight. The coordinated search tries two-state changes where
one-state changes stall. It recovers all four seven-grade losses.
Across the 360 seven-grade rows with simulated grading error, one-state
search attains the exact forecast optimum in 218 and coordinated search
in 307. The latter evaluates at most 290 chair tables across its local
passes. Exhaustive search evaluates 864. The independent optimum audit
is outside the local search count. The forecast optimum can still lose
under the true grade bank.

## Give adaptive and fixed routing the same information

Both interval selectors know the same seven grades, the same review
uncertainty interval and the same advertised prior. The interval team
can choose coordinated, fixed or silent actions. The interval fixed
control can choose fixed or silent actions.

| Routing policy | Wins vs. same-information fixed | Losses vs. same-information fixed | Mean net gain vs. same-information fixed | Below fully informed silence on documentary points |
| --- | ---: | ---: | ---: | ---: |
| Coordinated, point grade | 327 | 12 | +0.0775 | 125 |
| Interval-optimized fixed | 0 | 0 | 0 | 115 |
| Interval-optimized team | 278 | 3 | +0.0743 | 98 |

These are 360 modeled conditions on 20 score banks. The interval team
selects an adaptive action table in 281 rows. Against fixed routing
with the true bank and prior, it wins 209 and loses 145, with a mean
margin of −0.0149. The three same-information losses occur under
shifted inventory priors in synthetic banks. This supports a gain under
matched information and leaves sensitivity to prior error and scoring
uncertainty visible.
[Single-state protocol](protocol.md) · [Single-state results](results.json) ·
[Block protocol](block-protocol.md) · [Block results](block-results.json) ·
[Interval protocol](uncertainty-protocol.md) · [Matched-information results](interval-results.json)

## Replay the action tables through the record pipeline

The dispatcher executes each inventory and delivery branch for UNIFIL
and Myanmar in 12 inventory conditions. The chair's lookup uses the
public receipt mask. The responder's lookup uses its own inventory,
earlier attempted send and heard question. The dispatcher verifies
legal actions and reconstructs 16 final receipt masks using the actual
cached passage choices. All words match the reviewed records, and the
weighted release, send costs, query rates and receipt distributions
agree with the analytical scorer.

One Myanmar branch produces a 70-point record by requesting the chair
card, compared with 63 points from the fixed continuation. One UNIFIL
branch improves 49 to 63 with the same no-question observation and a
different responder action. These are exposed case records with
authored passage menus, simulated delivery, same-assistant marks and
zero fresh language generation.
[Runtime protocol](runtime-protocol.md) · [Weighted results and traces](runtime-results.json)

Run with the parent Python environment and import paths.

```bash
set -o pipefail
python3 policy_search.py | cmp - results.json
python3 block_search.py | cmp - block-results.json
python3 interval_search.py | cmp - interval-results.json
python3 delivery_runtime.py | cmp - runtime-results.json
```
