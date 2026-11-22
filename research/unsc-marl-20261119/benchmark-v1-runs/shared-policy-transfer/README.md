# Transfer the two learned desks between 2553 and 2721

**The receiving policy transferred in both directions. The forwarding
policy needed calibration on the target.** Both actors train from shared
terminal utility. Their inputs use the public price, delivery estimates,
the sender's own source coverage, and the frozen claim bit. The agents
share weights across source views. The receiver sees the bit only if the
message arrives. [Locked fit](protocol.md) · [Detailed policy outcomes](results.json)

| Docket used for training → held docket | Frozen team | 32 warm-start batches | 32 batches from zero | 128 randomized target exchanges, sender only | Exact target ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2553 → 2721 | 38.125 | 38.125 | 38.125 | **41.242** | 41.242 |
| 2721 → 2553 | 23.248 | 25.566 | 24.813 | **25.659** | 25.659 |

All columns average utility on the same 96 transport, cost and source-prior
settings per target. Factual release and forwarding cost are available
separately. The frozen 2553 sender sends nothing on held Afghanistan
settings. The frozen Afghanistan sender spends an average 10.058 points
on 2553, more than four times the target optimum. Replacing only the sender
with its best response restores the full 96-setting ceiling in each
direction. Replacing only the receiver changes nothing in either direction.

The 32-batch adaptation uses the same random draws for zero and warm
starts. Relative to the paired cold fit, the Afghanistan warm start
helps the 2553 target. The 2553 warm start still withholds throughout the
Afghanistan grid. A separate adaptive experiment then freezes the
transferred receiver and estimates the value of forwarding from 128
randomized target episodes. It uses recorded receipt flags and factual
scores. It conditions on the same source-coverage and claim inputs.
Every relevant cell is observed under this fixed design. The calibrated
sender matches the ceiling on 96/96 settings in both directions.
[Calibration design](calibration.md) · [Exploration log and support counts](calibration.json)

The 128 samples are enough to cover these deterministic source and
delivery-state combinations. This result does not establish a sample
requirement for other dockets, noisier judges, or a changed renderer.
The policy comparison varies both architecture and observation use.
The gradient fit reads only its internal agent observations and final
utility. The model-based calibration also reads delivery flags and uses
the declared independent transport model. It starts from a frozen
receiver and estimates target score differences directly. Its success
is conditional on those additional observations and the fixed partner.

The target docket is held out from policy training in the frozen column.
The historical cases, compiler, and claim extraction had been developed
on these families. The target calibration and warm-start columns use
target experience. The send price is constructed in score points.
Source policies train for 512 batches of 256 episodes, using one fixed
seed per direction and no tuning sweep. No further Qwen inference or
backbone updates occur.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B transfer_team.py --plan | cmp plan.json -
python -B transfer_team.py | cmp results.json -
python -B calibrate_sender.py --plan | cmp calibration-plan.json -
python -B calibrate_sender.py | cmp calibration.json -
```

[Previous joint fit and payoff archive](../documentary-team-policy/README.md)
