# Learn UN evidence routing from observed final scores

On Resolution 2744, a team that learned the value of delivered evidence
reached **40.4205** mean net points after **256 simulated episodes per
arm**, each with one terminal score. This was **1.0367** points above the
best arrival-only route and **1.8815** above the fixed route optimized for
the written rubric. The improvement appeared in 79 of 96 held channel,
cost and prior settings. It disappeared when the final writer changed.

| Compact writer without the admission filter | After 64 scores | After 256 | After 1,024 | After 8,192 |
| --- | ---: | ---: | ---: | ---: |
| Receipt-value team, with peer content | 37.0683 | **40.4205** | **40.4205** | **40.4205** |
| Receipt-value team, arrival only | 37.0683 | 39.3838 | 39.3838 | 39.3838 |
| REINFORCE, with peer content | 36.8750 | 36.8750 | 36.8750 | 38.0297 |
| REINFORCE, arrival only | 36.8750 | 36.8750 | 36.8750 | 37.9599 |
| Exact fixed rubric route, with peer content | 38.5390 | 38.5390 | 38.5390 | 38.5390 |
| Exact reviewed-score optimum, with peer content | 40.4205 | 40.4205 | 40.4205 | 40.4205 |

The previous sender fit required paired send and withhold scores under
the same draws. Here each episode supplies only the score and ID of the
record that actually occurred. The receipt-value estimator learns a
score for each observed combination of delivered passages. It uses the
known channel and price to compute local policies through centralized
training. The sender sees its own passage. The reply desk sees either
the presence of a note or its archived semantic code. Both know the
public channel settings and price. Neither sees other private information
or gets feedback during evaluation.

The peer learner had seen 11 of 12 outcome cells at the 256-episode
checkpoint. It assigned the remaining cell the starting value of 35.
That missing observation did not prevent it from reaching the exact
peer optimum under the tested settings. The fixed rubric comparison
uses the same information but assumes the writer will preserve the
registered claims. The lower REINFORCE result is specific to this
seed, update budget and parameterization. The receipt-value team uses
additional outcome metadata and a known transition model, and can
optimize its reply on each public setting.

## Writer change

| Evaluation writer | Frozen peer fit | Frozen arrival-only fit | Exact peer optimum | Probability of a zero-score joint record, frozen peer |
| --- | ---: | ---: | ---: | ---: |
| Compact without admission filter | 40.4205 | 39.3838 | 40.4205 | 0.00% |
| Compact with admission filter | 40.4205 | 39.3838 | 40.5649 | 0.00% |
| Topic-guided with admission filter | 22.6755 | 27.5144 | 37.2417 | 25.35% |

In the topic-guided replay, both formerly productive comparisons now
release zero. The same decisions that help the compact writer select
those failed records. A fixed route optimized on the written rubric also
loses its advantage under that swap. The failure sets up a direct test of
refreshing the learned receipt values with new single-trajectory
feedback while falling back to a source-only record during the refresh.

## Evidence and replay

This is centralized training with decentralized execution and a
12-state deterministic archive. Training and held tests use the same
exposed docket. The latter vary the channel, fees and priors. The
writer-swap test changes held score tables without refitting. All reward
labels are from earlier assistant review. The 256 episodes are simulator
lookups and required zero additional model calls or language-model weight
updates. Real stochastic generation and unseen families remain untested.

The replay reproduces byte for byte. An independent branch enumerator
checks all 192 held arm optima on the compact bank against the 256-episode
policies and the archived oracle means. It checks all 32,768 recorded
terminal rewards and reconstructs the receipt estimators. The initial
verifier import collided with a legacy module named `fit`. A path-based
load corrected the verifier without changing the fit.

[Protocol](protocol.md) · [Input pins](plan.json) · [Results and training traces](results.json) · [Verification](verification.json) · [Previous paired-credit fit](../native-reward-routing-fit/README.md)

From this directory in the project Qwen environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B fit.py --plan | cmp plan.json -
python -B fit.py | cmp results.json -
python -B verify.py | cmp verification.json -
```
