# Learn the value of forwarding before choosing whether to send

Learning the gain from delivery directly eliminated all 20 sender
errors on Resolution 2553, including the 18 Belgium cases. On 2721
it matched the oracle in 94 of 96 settings. Across both dockets,
the learned pair averaged **33.4502**, within **0.00035** of the
exact content-aware ceiling and above the 32.8936 arrival-only baseline.

| Sender update, with the reply policy also learning | 2553 utility | 2721 utility | Pooled utility |
| --- | ---: | ---: | ---: |
| Original sampled REINFORCE | 25.5228 | 41.2289 | 33.3758 |
| Sampled REINFORCE, twice the batch | 25.5195 | 41.2153 | 33.3674 |
| Paired send/withhold policy gradient | 25.5167 | 41.2301 | 33.3734 |
| Exact expected gradient | 25.5195 | 41.2423 | 33.3809 |
| **Learned delivery-value sender** | **25.6588** | **41.2416** | **33.4502** |
| Best arrival-only, optimized for each setting | 25.5839 | 40.2032 | 32.8936 |
| Content-aware oracle | 25.6588 | 41.2423 | 33.4506 |

Both paired branches reuse delivery and receiver draws. For the
policy-gradient variant their difference estimates the marginal reward
of sending. A sampled sender update, a doubled batch, paired gradients
and exact gradients all miss the 18 profitable held Belgium sends.
The exact-gradient policy also withholds in all seven beneficial
training contexts for Belgium. This rules out sampling variance as
a sufficient explanation in this setup. The original linear features
can represent the exact sign boundary.

The delivery-value variant instead estimates the incremental final
score from a delivered first note, using two running means per
private view for whether the reply is delivered. The sender
multiplies by the estimated channel probabilities and subtracts
the known attempt cost. The reply policy keeps a sampled
shared-reward update while the value model is learned. A fixed
two-point temperature governs sender exploration during training.

The value model and paired-gradient comparison use the same
262,144 nominal terminal score queries, 512 parameter updates and
single seed. All score queries reuse previously measured and
cached Qwen-derived comparisons. The exact-gradient diagnostic
integrates that fixed simulator rather than sampling it. An initial
paired run stopped at a shape mismatch in a diagnostic. Matching the
cost slice to its delivery mask fixed the assertion before collecting
the replayed results.

The value learner wins 18 of 96 settings on 2553 and ties the other
78. On 2721 it wins 74, ties 20 and loses two against best arrival-only.
Its optimized comparison with a fixed reply remains worse than the
learned team. These are structured policy updates on exposed dockets
with native relation scores. The value learner uses observed delivery
branches of a simulator with independent channels and known costs.
It still needs tests on unfamiliar event families, noisy terminal
scores and conversations where alternate branches cannot be replayed.

[Paired comparison](results.json) · [Exact-gradient diagnostic](exact-gradient.json) ·
[Delivery-value training and held evaluation](value-results.json) ·
[Paired protocol](protocol.md) · [Value protocol](value-protocol.md)

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B experiment.py --plan | cmp plan.json -
python -B experiment.py | cmp results.json -
python -B exact_gradient.py | cmp exact-gradient.json -
python -B value_sender.py --plan | cmp value-plan.json -
python -B value_sender.py | cmp value-results.json -
```

All new optimization runs use NumPy on CPU. There are no new model
calls. The earlier language-model stages used an AMD EPYC 9575F
64-Core Processor and an NVIDIA RTX PRO 6000 Blackwell Server Edition
as reported in their own receipts.
