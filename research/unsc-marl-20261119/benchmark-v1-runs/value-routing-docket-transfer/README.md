# Transfer delivery-value learning to Resolutions 2664 and 2739

The same delivery-value learner, initialized from scratch, matches the
content-aware oracle on **188 of 192** original-price settings and
**192 of 192** lower-price settings. At the original prices, the
arrival-only control also matches the oracle. At lower prices on 2739,
the learned pair beats arrival-only in **80 of 96** settings and ties
the other 16.

| Held group | Delivery-value team | Sampled team, same query budget | Best arrival-only | Content-aware oracle |
| --- | ---: | ---: | ---: | ---: |
| Original prices, 2664 | 37.6271 | 37.6246 | 37.6296 | 37.6296 |
| Original prices, 2739 | 37.7720 | 37.6250 | 37.7720 | 37.7720 |
| Lower prices, 2664 | 40.3156 | 40.3156 | 40.3156 | 40.3156 |
| Lower prices, 2739 | **40.0837** | 37.6250 | 39.7238 | **40.0837** |

Two document replies trade standalone coverage against a relational
bonus. On 2664 the choices are the adoption-time expiry terms or the
monitoring safeguards relevant to India's explanation. On 2739 they
are the operative reporting extension or the sponsors' reasons.
A constrained source renderer preserves facts available to the chair.
The experiment reallocates existing evidence and retains the original
rubric weights. Since the document desk can send only one of the
alternatives, the best complete receipt combinations score 60 and 56
out of 70 in this allocation.

The same frozen Qwen source judge correctly distinguishes the ten
full and partial cards. Its two mapped margins compose to the same
authorized comparison as the authored key on all 12 paired records.
The closest decision is the objection-only 2739 note at −0.125.
It preserves the reason for Algeria's abstention, and the evidence
for a shared reporting purpose is absent from that excerpt.
The full note supports both claims.

At the original held prices of 8, 11 and 15, it never pays to send
that partial objection on its own. The optimal sender's decision
to transmit therefore gives away the useful receive class. The
receiver can ignore content and still choose the matching reply.
The separate prices of 1, 3 and 5 were locked before model outputs
were read. They allow the objection-only note to pay. The learned
receiver chooses the reporting rationale for the full note and
the operative clause for the objection-only note. This yields
a mean gain of 0.360 points on 2739 over the optimized arrival-only
control. The 2664 structure still has no oracle gap between the two
visibility conditions.

Both training arms use 512 updates and 262,144 nominal cached
terminal queries. The seed, training prices of 6, 12 and 18 and
training channel probabilities match the earlier method. The existing
report writer calls the new sampled arm `archival_fit`. Neither arm
uses the original dockets' fitted policy weights.

The sole first-token worker collected 20 judgments using an
eight-thread AMD EPYC 9575F 64-Core Processor on Aurora. Earlier
drafting runs used an NVIDIA RTX PRO 6000 Blackwell Server Edition.
This run measures re-training the method on two additional but
previously exposed cases. The payoff tables use a typed renderer
and authored item weights. Independent judgments, unseen event
families, online free-text rewards and changes to the closed
benchmark remain outside this trial.

[Locked prompts and allocations](plan.json) · [Native token trace](verified.json) ·
[Original prices and exact rendered records](results.json) ·
[Lower-price holdout](lower-price-results.json) · [Protocol](protocol.md)

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_transfer_dockets.py plan | cmp plan.json -
python -B collect_transfer_dockets.py verify | cmp verified.json -
python -B fit.py | cmp results.json -
sha256sum -c lower-price-lock.sha256
python -B lower_price.py | cmp lower-price-results.json -
```

Use the existing Aurora Qwen runtime. Verification only needs the
stored evidence and tokenizer.
