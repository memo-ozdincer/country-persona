# Verify the final record across the reserve and transfer panels

Render the checked outcome of a fictional workshop from the
authenticated receipts that actually reached the chair. Each
record gives the two named role reports or their absence, cites the
fixed historical record through verbatim excerpts, states the grade
rule and explains whether the same disposition holds across all
compatible completions. A known impasse has a zero in every possible
package. An unresolved result can include feasible packages whose
outcome sets have no common member.

The separate verifier reads the emitted text and recomputes all
compatible outcomes from the public possible-card decks. It checks
the status, underlying excerpts, reported grades, completion counts,
scope, and exact unresolved outcome sets. It requires the 165-word
cap and rejects a claimed unique package whenever the report's
contract only proves a shared winner. The renderer consumes already
authenticated input; it does not authenticate messages on its own.
The official excerpts come from the archived outer-space, Mali and
Myanmar packets. [Protocol](protocol.md) · [Renderer](render.py)

## Verified output

- All 117 reachable receipt views rendered and passed verification.
  The longest reachable record has 158 words.
- The independent verifier checked 367 legal receipt combinations,
  including 32 whose compatible worlds contain a tied winner set.
- It rejected 2,362 altered reports or malformed inputs, including
  wrong grade attribution, changed historical text and unsound
  completion claims.
- The rendered-outcome replay reproduces the earlier, separately
  graded grid-198 literal results under both prior mixtures.

The 70-point column measures mechanical documentary coverage under
the fixed rendering contract, including faithful deferrals. Settled
points count that coverage only when the exact verifier establishes
a package or impasse. Wider-panel 70 scores are software results.
They have no independent prose judgments.
[Records and paired trajectory weights](results.json) · [Preparation notes](preparation.md)

## Choose whether to use the ranked recipient

The unqualified 32-observation switch uses the learned recipient
whenever balanced worlds look more likely. The payoff selector
instead switches only when the ranked choices are forecast to
improve expected certified outcomes. It uses the same ordinary
histories, public possible-card model and known candidate mixtures.
Weights, messages, final records and fees stay fixed.

| Evaluation panel | Fixed, settled /70 | Mixture-only switch, settled /70 | Payoff selector, settled /70 |
| --- | ---: | ---: | ---: |
| Four outer-space reserve grids | 54.1181 | 54.2509 | 54.2509 |
| Mali and Myanmar, canonical orders | 55.2956 | 55.1505 | 55.2956 |

The payoff selector uses the learned recipient only on the affected
outer-space grid. It retains the mean reserve gain of 0.133
settled points, or about 0.00190 normalized net at the same message
fees. It keeps the fixed policy on both transfer grids. The benefit
remains concentrated on one previously selected positive grid.
It depends on a declared predictive model for the possible regimes
and the verifier. No model generation, weight update, or new source
family was part of this test.
[Selector protocol](choice-protocol.md) · [Per-regime rank probabilities](policy-choice.json)

## Run

Use the project Python environment with NumPy and PyTorch.
The command returns a report only after it passes the verifier.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python render.py 198 '[["A",0],["A",3]]'
python replay.py | cmp results.json -
python policy_choice.py | cmp policy-choice.json -
```
