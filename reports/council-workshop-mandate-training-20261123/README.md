# Train against feasible agreements and certified impasses

A shared speech policy trained on the exact workshop reward rejected bad
deals that a unanimity-reward policy accepted. The verified-reward policy
solved **342 of 386** evaluation episodes. The unanimity-reward policy
solved **75 of 386** and reached an invalid agreement in all 193
infeasible episodes.

| Test cohort | Verified reward | Unanimity reward | Checked script |
| --- | ---: | ---: | ---: |
| Held three-seat profiles, three packages | 128/128 | 33/128 | 128/128 |
| Five seats, three packages | 115/128 | 20/128 | 115/128 |
| Five seats, four packages | 97/128 | 22/128 | 97/128 |
| Two existing climate workshops | 2/2 | 0/2 | 2/2 |

Each arm uses 16,384 sampled episodes on the same three-seat training
profiles. A single linear head is shared across seats. It observes
whether the candidate action concerns a package allowed by that seat's
mandate, the current draft, public exclusions and public acceptances.
Each episode supplies one shared outcome to a length-scaled
policy-gradient update. The verified arm rewards either a valid deal or
a certified impasse. The proxy rewards any unanimity. Neither arm uses
language model calls or updates Qwen. The speech schedule is fixed.

The three-seat split groups mandate profiles under seat permutations and
package relabelings before sampling. The five-seat and four-package
cohorts change the roster size or menu size. Every synthetic cohort
balances feasible and infeasible draws. These are repeated draws of
structured mandates, with one training seed. The earlier climate cases
are exposed examples kept out of this fit. Their terminal reward remains
one for either correct outcome.

## Mandate sensitivity and budget failures

In nine paired states, four other seats already accepted the same
package. Adding that package to the next seat's private mandate is
the only change. The verified policy avoided an invalid accept in
**9/9** cases and accepted an allowed package in **3/9**. The proxy
accepted in both members of all nine pairs. The verified policy often
spent the extra turn ruling out an alternative even when accepting
would have completed a valid deal. The checked-exchange script matched
its aggregate scores across all original cohorts.

A post-fit reference rule prioritizes the current draft. It correctly
changes its decision across **9/9** local pairs, and it finds 10 more
four-package agreements than the learned policy. It loses 27
four-package impasse certifications. This exposes a trade-off between
finishing a promising agreement quickly and gathering enough information
to certify an impasse. A centralized reachability calculation finds
that 43 of the learned policy's 44 failures could have been solved
within the same nine speeches with full mandate information. Only one
infeasible world could not make the required exclusions and declare
an impasse in time.

The production audit replays both fits and the post-fit rule on all
386 episodes. It shows identical final outcome, selected package and
speech count between the training transition loop and the regular
workshop runner under the same rotation. It also checks the rule for
every local contrast and computes the optimistic cap bound. This is
evidence about a small structured policy. Language-agent behavior,
independent opponent strategies and open-text transfer remain open.

[Training traces and held scores](results.json) · [Production replay and decision contrasts](audit.json)

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-mandate-training-20261123
python3 -B research/council_workshop/train_mandates.py | cmp "$out/results.json" -
python3 -B "$out/audit.py" | cmp "$out/audit.json" -
```
