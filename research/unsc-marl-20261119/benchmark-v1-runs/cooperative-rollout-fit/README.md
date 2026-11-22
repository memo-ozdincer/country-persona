# Learn from shared documentary returns in a UN evidence relay

The chair chooses whether to request a card using the public receipt
mask. The responder chooses a card or silence using its private
inventory, original transmission and heard request. The simulator
scores the resulting UN record and charges communication attempts,
including lost messages. This experiment uses fixed opening policies
and compares the same announced score and inventory information
throughout. All training is on CPU from synthetic reward banks. The
five held UN case banks are exposed archival records disjoint from
the fitting banks up to an additive score shift.
[Protocol](protocol.md) · [Locked banks and configurations](plan.json)

## Learn action values from paired rollouts

Three alternating updates fit each actor to the gain of a legal action
over silence under matched inventories and delivery draws. The two
residual heads use only the announced forecasts and role observations
at execution. Over 48 training banks, three inventory laws and three
review perturbations, the six fits use 497,664 inventory and delivery
draws. Every legal alternative contributes an action sample. No
oracle action label enters fitting.

On 90 held conditions, the fitted team beats the matched-information
fixed policy in 52 with a mean net gain of +0.0196. It loses 86 and wins
four against the neutral implementation of its own policy, averaging
−0.0593, and falls below informed silence in 28 conditions. The
responder-only change incurs nearly all of the extra message cost.
The fitted chair alone loses 17, wins 11 and ties 62 against the neutral
policy. Lower training residual error did not translate to held reward.
[Learned weights and all conditions](results.json) · [Component swaps](components.json)

## Fit the uncertain reward entries

The follow-up learns corrections only for the reviewed pair grade and
the inferred full-receipt grade. It fits 36 of the synthetic banks and
chooses the single correction strength on the other 12. Validation
selects half strength. The remaining score entries and opening
policies stay fixed. The actor tables are recomputed from the learned
forecast using the neutral policy construction.
[Reward protocol](reward-protocol.md) · [Fitted reward model and held results](reward-results.json)

| Held comparison | Wins / ties / losses, selected correction | Mean net change |
| --- | ---: | ---: |
| Neutral with the same actor construction | 25 / 49 / 16 | +0.0052 |
| Fixed targeting with the announced forecast | 69 / 7 / 14 | +0.0841 |
| Exact adaptive planning with the announced forecast | 15 / 14 / 61 | −0.0060 |
| Fixed targeting with true scores and mixture | 62 / 1 / 27 | +0.0213 |

The half-strength correction reduces the below-silence count from 15
to 10 compared with the neutral policy. Full strength lowers that count
to five and gives a smaller mean net gain of +0.0021. Its strength was
not chosen by the held rows. Both effects are small in rubric-point
units. An independent dispatcher reconciles all 180 fitted and corrected
held policy outcomes against the reward formula.

## Combine learned values with live re-review

With the previously admitted live pair grades, the neutral actor
construction still falls below informed silence in 12 of 23 triggered
rows. Correcting only the inferred full-record grade leaves those
12 failures and lowers mean net by 0.0146. Allowing the predictor
to overwrite the admitted pair score removes the 12 quality failures
but lowers mean net by 0.0122. The existing reviewed adaptive search
also has zero quality failures and improves mean net by 0.0046
over the neutral actor on the same reviewed records.
[Verified-review protocol](reviewed-protocol.md) · [Dispatch and outcomes](reviewed-results.json)

A matched planner replay tests the inferred-grade correction inside the
same reviewed robust search. It recomputes the unmodified reference in
all 15 distinct planner contexts and matches the archive. The learned
forecast keeps the confirmed pair grades and the original uncertainty
scenarios. It produces zero below-silence outcomes, the same mean
documentary release, and a net change of −0.0040. It wins two, ties
15 and loses six of the 23 rows. The fitted reward model helps modestly
under noisy inputs in the simpler actor construction. On these reviewed
records the unmodified robust planner retains the stronger mean net.
[Matched search protocol](search-protocol.md) · [Matched planner replay](search-results.json)

## Replay

Run from this folder in the Aurora Qwen Python environment with SciPy
available for the final robust replay. The experiments use simulation
only. The scripts reproduce fitting weights, selected strength, archived
held policy tables and rewards.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
"$py" rollout_fit.py plan | cmp plan.json -
"$py" rollout_fit.py run | cmp results.json -
"$py" components.py | cmp components.json -
"$py" reward_fit.py | cmp reward-results.json -
"$py" reviewed.py | cmp reviewed-results.json -
"$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path("search_reviewed.py",run_name="__main__")' "$scipy_packages" | cmp search-results.json -
```
