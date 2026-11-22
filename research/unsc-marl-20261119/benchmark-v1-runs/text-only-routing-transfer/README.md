# Transfer a routing policy from other UN dockets using source text

A receipt-value policy fit on Resolutions 2721 and 2744 scored
**39.859** on the original Resolution 2417 cards, above the exact
arrival-only bound of **39.457**. It dropped to **37.504** on paraphrases
of the same target cards. The fixed semantic rule reached **40.565**
on the original and **39.728** on the paraphrases. The target pair keys
were excluded from fitting and policy selection.

| Routing policy with peer access | Original wording | Both cards reworded |
| --- | ---: | ---: |
| Donor fit, 64 episodes per docket | 38.699 | 37.672 |
| Donor fit, 256 episodes per docket | 39.859 | 37.504 |
| Unfitted conjunction of two model features | 40.565 | 39.728 |
| Fixed word overlap | 39.728 | 39.728 |
| Best arrival-only on the reviewed outcome table | 39.457 | 39.457 |
| Exact peer optimum on the reviewed outcome table | 40.565 | 40.565 |

The donor fit uses 10 unique double-delivery scores, reached through
512 simulated trajectories across the two fitting dockets. Its target
comparison estimates compress into a narrow range. With the original
cards, replacing the send decisions while keeping the fitted replies
raises utility to **40.457**. Replacing replies alone gives no gain.
With paraphrases, improving the replies alone yields **39.936**, while
improving just the sender yields **38.432**. The semantic conjunction
also assigns a high bonus to three of four fictional contrasts with
zero reward under the original rubric. Some could support a different
useful comparison in their fictional scenario.

The policy uses known possible views, public clause choices and
standalone values. Its private state is the view actually drawn,
revealed to the second desk only in the peer arm when the opening
arrives. Both desks know the transport and send fee. The evaluator
uses the existing source-bound reward table. Target labels were
removed in an independent replay of every route. This was an exposed
project docket and an offline routing comparison. Novel draft
certification, externally reviewed scores and unseen-family transfer
remain open.

Frozen Qwen3.5-4B performed 104 first-token forward reads on an NVIDIA
RTX PRO 6000 Blackwell Server Edition, with 23,072 input tokens across
all examples. Each pair uses four reads. The worker exited normally.
The net score includes simulated sending fees. It excludes inference
fees and latency.

[Locked protocol](protocol.md) · [Feature verification](verification.json) ·
[Fit and frozen actions](fit.json) · [Scores](results.json) ·
[Component swaps](attribution.json) · [Leakage audit](audit.json)

Run in the Aurora environment from this directory:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B extract.py verify | cmp verification.json -
python -B fit_transfer.py plan | cmp train-plan.json -
python -B fit_transfer.py fit | cmp fit.json -
python -B fit_transfer.py score | cmp results.json -
python -B attribution.py | cmp attribution.json -
python -B audit.py | cmp audit.json -
```
