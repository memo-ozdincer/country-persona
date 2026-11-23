# Give the learned workshop policy a speech budget

A budget-aware policy recovered additional valid agreements at short
caps. It also tried nine unacceptable signatures that ended in invalid
agreements. A post-fit check that removes only out-of-mandate acceptance
prevented every invalid agreement and preserved all of the new valid
outcomes. The blocked episodes stayed unresolved.

| Speech cap | Budget-blind fit | Checked script with final-signature rule | Budget-aware fit with mandate check | Raw budget-aware invalid agreements |
| --- | ---: | ---: | ---: | ---: |
| 6 | 210/386 | 211/386 | **215/386** | 6 |
| 9 | 342/386 | 344/386 | **347/386** | 3 |
| 12 | 382/386 | **384/386** | **384/386** | 0 |

The treatment and control both train on the same three-seat profile
pool, capped at 5, 7, 9 or 12 speeches. Each uses 16,384 simulated
episodes, the same seed and the exact shared success reward. The
budget-aware treatment adds publicly calculable features. They encode
whether an action closes the draft now, whether remaining seats can
still accept or exclude every remaining option in time, and how many
rounds remain. The policies get only their own mandate and the public
state. The checked script uses the earlier exclusion policy, with an
extra rule to immediately complete a locally permitted last signature.

The held panels resample the earlier profile split with a new fixed
seed and retain the two exposed climate workshops. The same worlds
appear at all three speech caps. Gains are counts on paired cases and
are not independent across caps. All added successes are valid
agreements. The budget-aware policy and the fixed script certify the
same number of impasses at each cap. The tail of four-package and
five-seat agreement searches continues to hit the time budget.

The mandate check is an explicit post-fit intervention in the
diagnostic. It uses each seat's own mandate to bar an incompatible
acceptance from its action list. In all nine affected episodes it
changed the terminal result from invalid agreement to unresolved.
It neither manufactured an agreement nor certified an impasse.
The raw-policy results and attempted violations remain visible. The
check is not part of the live open-text workshop or the reward label.

These are structured policy results with one seed and a fixed speech
rotation. There were no language-model calls or model-weight updates.
The earlier nine-speech training result still reproduces byte for byte.

[Training and per-episode results](results.json) · [Mandate-check audit](audit.json)

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-budget-policy-20261123
python3 -B research/council_workshop/budget_policy.py | cmp "$out/results.json" -
python3 -B "$out/audit.py" | cmp "$out/audit.json" -
```
