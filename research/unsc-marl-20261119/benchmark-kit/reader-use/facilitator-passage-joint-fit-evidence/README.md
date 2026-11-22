# Learn source disclosures and follow-up together

The 96-update joint fit reproduced the greedy actions of the 96-update fixed-opening control. A single follow-up fit began without a bonus on the reference action and learned those same opening choices. Its small differences on correlated inventories follow the requester and responder in component swaps. Direct planning improved modeled net reward over both fits in every condition while asking fewer questions.

| Evaluation case | Inventory law | Fixed opening | Joint fit | Joint fit with weaker start | Declared-channel planner | Hindsight planner |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Resolution 2719 | Uniform | +0.696 | +0.696 | +0.696 | +0.950 | +0.950 |
| Resolution 2719 | Correlated duplicates | +0.242 | +0.242 | +0.246 | +0.601 | +0.601 |
| Resolution 2504 | Uniform | +0.832 | +0.832 | +0.832 | +0.937 | +1.154 |
| Resolution 2504 | Correlated duplicates | +0.143 | +0.143 | +0.157 | +0.560 | +0.694 |

The table gives expected net points above exact hindsight no-request. All policies face the same message costs and measured source-certificate replay. The declared planner chooses maps assuming ideal certificate delivery, then is scored against observed admissions. The hindsight planners use observed admissions for map selection as well. Each planning block is exact conditional on the other block. Alternating the blocks can leave different stationary policies, as in the Resolution 2504 correlated replay. The fitted rows ask once per episode. The declared planner asks 0.658–0.679 times. Stochastic evaluation also favors the fixed-opening fit over both joint fits in all four rows.

All three fits use the same 30 archived development banks, two inventory priors and perfect admission during fitting. The reference policy comes from exact no-request optimization under that same admission model. The weaker initialization sets its action bonus to zero and retains the reference action as a feature. It improves mean soft training reward from 46.868 to 53.043. Reference-start joint training moves from 51.512 to 53.227, and fixed-opening training from 51.566 to 53.228. Outputs use the terminal checkpoint.

## Swap planner and fitted components

Replacing only the two opening maps gains 0.157 and 0.098 points over the fitted team on Resolution 2719. On Resolution 2504, it ties the fit under uniform inventories and gains 0.232 under correlated inventories. Replacing only follow-up under the last condition drops net reward to 4.278 points below no-request, compared with 0.560 above no-request for the complete planner. This swap combines maps optimized with different opening distributions. It shows that the value of the follow-up depends on the opening policy, so an opening-only intervention can miss the gains from co-adaptation. [Matched component replay](planner-swap.json)

## Opening feature capacity

The audit fits one linear weight vector per sender to the declared planner's preferred opening action for each of the eight local inventories in each evaluation condition. The comparisons cover all legal alternatives. Maximizing the minimum preference gap with weights in the unit box finds a positive strict margin of 0.001585 for the left sender. The right sender's pooled strict margin is zero. A solution achieves exact argmax behavior with the implementation's lowest-index tie rule. Its feature weights are zero except for the nonempty-send indicator, so tied sends follow that rule. This is a fit to the observed planner decisions on the evaluation rows. It gives an expressivity check for the opening features on these rows and leaves margins, learnability and transfer open. The audit covers opening features only.

## Evidence and replay

- [Initial comparison protocol](protocol.md) and [fit traces and outcomes](results.json).
- [Weaker initialization protocol](weak-start-protocol.md) and [fit trace and outcome](weak-start.json).
- [Opening feature differences and optimization witnesses](capacity.json).
- [Resolution 2719 and 2504 passage evidence](../facilitator-passage-routing-evidence/README.md) and [Resolution 2504 procedural repair](../facilitator-procedure-passage-evidence/README.md).

Run from this benchmark's `reader-use` directory with repo `src` on `PYTHONPATH`. The first two scripts use NumPy and CPU PyTorch. The capacity audit also uses SciPy with HiGHS.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_passage_joint_fit.py | cmp facilitator-passage-joint-fit-evidence/results.json
python facilitator_passage_joint_initialization.py | cmp facilitator-passage-joint-fit-evidence/weak-start.json
python facilitator_passage_joint_capacity.py | cmp facilitator-passage-joint-fit-evidence/capacity.json
python facilitator_passage_joint_swap.py | cmp facilitator-passage-joint-fit-evidence/planner-swap.json
```

The two cases were previously examined and excluded from the fitting banks. These are structured communication policies evaluated over modeled delivery and authored evidence scores. No language model parameters were updated and no new final records or independent annotations were collected here.
