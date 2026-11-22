# Jointly train two desks with native source-claim rewards

A frozen Qwen3.5-4B source verifier labels **6/6 real 2553 pairs** and
**6/6 withheld contrast probes** correctly. It recovers shared UK–Germany
concerns about rushed negotiations and distinguishes Belgium's funding
argument from Germany's position on Fund management. The six probes
include four reversals or quotation traps and two positive paraphrases.
They contribute no rewards to training.

The two-desk fit uses measured native relation bonuses for 2553 and
the prior native results for 2721. All 12 double-delivery rewards
match the authored reference. Using them for 512 joint REINFORCE
updates reproduces the recorded weights, gradients and utility
checkpoints from the authored fit under the same seed. The six reform
records also pass the frozen quote-span validator. The native judge
chooses a typed clause and the renderer preserves the other sourced
text. The standalone scores and decoder observations are inherited.

| Held settings | Native-reward trained team | Best arrival-only | Fixed reply partner | Same learned reply with optimal sender |
| --- | ---: | ---: | ---: | ---: |
| Both dockets, 192 settings | **33.376** | 32.894 | 31.415 | 33.451 |
| Resolution 2553, 96 settings | 25.523 | **25.584** | 25.092 | 25.659 |
| Resolution 2721, 96 settings | **41.229** | 40.203 | 37.739 | 41.242 |

The arrival-only control can optimize sends and choose different replies
for arrival and silence. The pooled advantage comes from 2721. On
2553, the learned sender makes 18 suboptimal choices on the Belgium
view and two on the UK explanation view. Optimizing sends while
holding the learned reply policy fixed closes the entire remaining
oracle gap. This is an exact outcome-table diagnostic. It identifies
where the joint fit falls short even with exact rewards.

The score table came from frozen language-model judgments observed
before routing training. The analysis measures two-agent learning with
model-derived typed rewards on exposed case material and simulated
delivery. The learning updates affect the decentralized policy weights.
The language-model checkpoint stays frozen, with no reward from
unconstrained final prose. The paraphrases and reversals are
same-project controls, and the held settings vary transport, price and
prevalence on the same two dockets.

All 44 new native label reads completed on Aurora on an eight-thread
AMD EPYC 9575F 64-Core Processor, matching the prior 2721 judgment
backend. Some earlier drafting and typed controls used NVIDIA RTX PRO
6000 Blackwell Server Edition. Benchmark v1.6 remains frozen.

[Locked prompts](plan.json) · [Verified logits](verified.json) ·
[Training history and utility](results.json) · [Rendered finals](native-records.json) ·
[Sender diagnosis](sender-ceiling.json) · [Worker receipt](evidence-cpu/launch.json)

From this directory in the existing Aurora Qwen3.5 environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_transfer.py plan | cmp plan.json -
python -B collect_transfer.py verify | cmp verified.json -
python -B fit.py | cmp results.json -
python -B render.py | cmp native-records.json -
python -B sender_ceiling.py | cmp sender-ceiling.json -
```
