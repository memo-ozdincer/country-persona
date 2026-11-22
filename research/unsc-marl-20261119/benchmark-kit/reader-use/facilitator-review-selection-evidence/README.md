# Target reviews that can change the chair's requests

Start with an assessed public record and three assessed singleton records. The chair retains the earlier nominal opening model and the same independent third-send fallback across all policies. It chooses between requesting an authorized missing card and staying silent. The eligible review items are the three paired receipt records and the full record. [Frozen protocol](protocol.md) · [Review implementation](../facilitator_review_selection.py)

The unknown scores are integers from zero to 70 and are monotone by receipt inclusion. They carry the separately defined 21-point completion bonus at 70. Split that nonlinear condition into the possible patterns of which records receive full credit. Within each pattern, policy-return differences are linear in the unknown scores. Equalities and known endpoints suffice at a maximum. The implementation therefore loops over score sets formed from the anchors and the 0, 69 and 70 endpoints, filtering for monotonicity. The audit compares this reduction with every feasible integer value on three small grids, two priors and six fallback tables. [Independent enumeration](audit.json)

The request policy minimizes worst relative regret per opening state. Summing those state-wise worst regrets gives an upper bound relative to a nominal planner given the full score bank. The next review is chosen to minimize that bound after the worst admissible answer to the review. The evaluator then reveals the actual archived or authored label for that record. Score actual opening teams separately, using exactly the same fixed third-send fallback. [Every label acquisition and policy result](results.json)

## Results

The experiment evaluates 72 conditions. These cross six real-content archival banks and twelve authored conjunction or full-score foils with two priors and two opening teams. The targeted, fixed-order and highest-visitation strategies all use the same policy planner.

| After two additional reviews | Targeted regret reduction | Fixed order | Highest visitation |
| --- | ---: | ---: | ---: |
| Mean worst-case nominal regret bound | 0.356418 | 0.530615 | 0.535808 |
| Mean realized regret under nominal openings | 0.046558 | 0.138358 | 0.179678 |
| Mean net on the actual opening teams | 53.605941 | 53.604249 | 53.461419 |
| Conditions with a bound of 0.5 points or less | 66/72 | 32/72 | 40/72 |

All strategies start with a mean worst-case bound of 3.572770. Targeted review needs 2.08 additional records on average to reach a half-point bound, compared with 2.56 for fixed order and 2.44 for highest visitation. At the more stringent quarter-point threshold it still needs 2.78. The gains chiefly reduce uncertainty about the reward. Actual net is almost tied with fixed order after two reviews. On the six archived banks, the singleton-corrected point estimate already matches full-bank nominal planning. The synthetic foils test the missing interactions that those archives alone would underrepresent. [Review budgets and grid checks](audit.json)

The bound depends on the nominal inventory and opening model, the fixed fallback and monotone scores. Free-form drafting can violate monotonicity when added text creates a serious error. The test uses reviewed fixed record banks and explicit monotone controls. Reuse it where those assumptions are independently verified. Review counts measure labels acquired, with annotator time and agreement still unmeasured.

## Replay

From `benchmark-kit/reader-use`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python facilitator_review_selection.py
OPENBLAS_NUM_THREADS=1 python facilitator_review_selection_audit.py facilitator-review-selection-evidence/results.json
```
