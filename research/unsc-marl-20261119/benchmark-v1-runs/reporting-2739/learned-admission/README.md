# Learn cooperative admission of UN scope judgments

Train a proposer to forward a locally read relation and a reviewer to
confirm or veto it. Both share the same reward. They see the exact
candidate witness and the same claim. The two Qwen3.5-4B instances read
different option mappings. The proposer uses its own mapped logits.
The reviewer sees its own mapped logits and the categorical label
from the proposer. The chair can publish an admitted support or
contradiction. Unresolved is the default, including when the proposer
withholds. Neither policy can alter a model-proposed relation.

## Fit and archived validation

Use 19 previously observed claim rows from four event families.
Evaluate both desk orders and weight families equally. The 160 exact
CPU policy-gradient steps update two small heads over fixed Qwen
logits. Correct actionable admissions earn +1, wrong admissions
cost 2 points, and sending a label costs 0.05. Zero logits give a
stochastic net of 0.0569, which rises to 0.2867 on the full fitting
set. The fit checks each analytic gradient coordinate against a
finite-difference derivative.

| Rule | Held-family mean net | Relation accuracy | Wrong admissions |
| --- | ---: | ---: | ---: |
| Learned proposer and reviewer, greedy | 0.3263 | 73.13% | 9.38% |
| Learned proposer and reviewer, sampled | 0.2203 | 60.08% | 8.77% |
| Fixed agreement | 0.3888 | 76.25% | 6.25% |
| First desk alone | 0.2679 | 74.58% | 16.67% |
| Pooled mapped logits | 0.2229 | 77.08% | 22.92% |

The greedy fit always sends when the proposer has an actionable label
in these folds. Its net difference from the fixed agreement control
comes from reviewer choices. The difference is concentrated in Haiti.
In Mali, both mappings misread Russia's proposal for a final extension
as contradicting that exact attribution. The two-stage rule preserved
the common error.
[Protocol](protocol.md) · [Frozen weights and leave-one-family-out results](fit.json)

## Resolution 2739 with fresh source reads

Lock eight claims and their witnesses before collecting 16 new Qwen
reads. The claims cover both delegations' reporting positions, the
recorded votes, and overbroad interpretations of endorsement, military
authorization, and exclusive purpose. The original documentary relation
prompt stays fixed. Both model mappings receive the same normalized
source and claim. The candidate labels are outside model inputs.
[Held claims and keys](held.json) · [Plan and input hashes](plan.json)

| Rule | Net reward | Relation accuracy | Wrong admissions |
| --- | ---: | ---: | ---: |
| Learned proposer and reviewer, greedy | 0.4656 | 16/16 | 0/16 |
| Learned proposer and reviewer, sampled | 0.2742 | 84.96% expected | 4.57% expected |
| Fixed agreement | 0.4656 | 16/16 | 0/16 |
| First desk alone | 0.0906 | 13/16 | 3/16 |
| Pooled mapped logits | 0.2188 | 14/16 | 2/16 |
| Oracle with the same proposer label constraint | 0.4750 | 16/16 | 0/16 |

The fitted greedy policy always sends an actionable first label and
agrees with the fixed control on every review. It admits eight correct
decisive labels, rejects three false proposals and leaves the other five
contexts unresolved without a message. Switching the proposer mapping
creates unilateral false support for Algeria's endorsement of the
deadline, opposition to cessation, and the sponsors' use of reporting
as the exclusive purpose of the resolution. The other mapping correctly
returns unresolved on each. Both mappings leave unresolved the claim
that the sponsors explicitly expressed no position on military
authorization. A hindsight sender's only gain here is avoiding the
three unnecessary transmissions.

The primary result shows that peer validation helps when the two
readings disagree. The two-stage fit has no advantage over the fixed
agreement rule on these held probes. In the archived family folds it
has a lower net and more wrong admissions. Same-model agreement
also leaves the jointly wrong Mali attribution undetected.
[Policy outcomes and probabilities](results.json) · [Action-constrained ceiling and common errors](channel-audit.json)

The 16 probe forwards consume 4,932 input and 32 constrained output
tokens on NVIDIA RTX PRO 6000 Blackwell Server Edition. Frozen
language-model weights provide both views. The archived margins were
recorded on CPU. The classification keys and payoff are authored
from the observed archival sources. The held probe prompts are new
and the event is exposed. This measures evidence admission under
a modeled utility, with final-record transfer and independent review
still unmeasured. [Preparation receipt](preparation.md) ·
[Worker receipt](evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from the [case evaluation](../README.md#reproduce).
Set the project paths for the archived prompt adapter.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" team.py fit | cmp fit.json -
"$py" held.py fixtures | cmp held.json -
"$py" held.py plan | cmp plan.json -
"$py" held.py verify | cmp verified.json -
"$py" team.py evaluate | cmp results.json -
"$py" channel_audit.py | cmp channel-audit.json -
```
