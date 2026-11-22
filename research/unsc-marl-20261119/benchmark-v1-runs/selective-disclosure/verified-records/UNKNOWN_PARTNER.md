# Adaptation to unfamiliar partners from archived chair receipts

A recipient with 128 previous chair receipts earns **0.59971 net reward** using a selector driven by which partner rules can explain those receipts. The original two-rule library earns **0.59345** and the known-partner ceiling is **0.60005**. These are equally weighted means across 78 authored conditions on six exposed workshop grids.

The first study tests a library built around highest- and lowest-grade reporting. The recipient sees its own archived cards, delivered peer messages and first chair receipts. It can evaluate each of its three truthful reports against the verified final-record reward. It averages these counterfactual values within its local observation states with two prior observations’ worth of regularization. Archived reads are unpriced. In the original test, direct fitting improves on the library for median-grade and public-priority partners. The equal per-turn mixture favors the library, whose default is optimal there.

| Unfamiliar opener at 128 receipts | Channel | Two-rule library | Direct fit | Known-partner ceiling |
| --- | --- | ---: | ---: | ---: |
| Median grade | Silent | 0.57011 | 0.58396 | 0.58457 |
| Median grade | Shared | 0.53665 | 0.55142 | 0.55304 |
| Equal high/low mixture | Silent | 0.60265 | 0.60169 | 0.60265 |
| Equal high/low mixture | Shared | 0.57884 | 0.57810 | 0.57884 |

The follow-up adds uneven high/low mixtures. The selector uses the original posterior while either pure rule still explains the receipts. When both fail but all receipts remain possible under a mixture of the two, it switches actions only if the new action improves expected payoff at both ends of the central 80% interval for the mixture weight. A receipt outside that mixture’s support triggers direct fitting. This brings the shared-channel equal-mixture result to 0.57883 and the shared-channel median result to 0.55157 after 128 receipts. Direct fitting still leads the selector on the high-heavy silent mixture.

| Archived receipts | Two-rule library | Direct fit | Mixture rules only | Selector | Known-partner ceiling | Paired sampling SE |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.59123 | 0.59123 | 0.59123 | 0.59123 | 0.60005 | 0 |
| 4 | 0.59448 | 0.59222 | 0.59496 | 0.59605 | 0.60005 | 0.0000363 |
| 16 | 0.59361 | 0.59506 | 0.59456 | 0.59740 | 0.60005 | 0.0000397 |
| 32 | 0.59347 | 0.59697 | 0.59458 | 0.59842 | 0.60005 | 0.0000323 |
| 128 | 0.59345 | 0.59931 | 0.59466 | 0.59971 | 0.60005 | 0.0000131 |

The standard error tracks paired sampling of 1,024 simulated histories per condition. The scenario panel is fixed. All deployment scores use the same mechanically certified records, and certificate values were checked against the independent decision computation. The study measures recipient adaptation to stationary partner distributions. Within-negotiation changes, access costs for these partners, transfer to unseen dockets and language quality remain unmeasured. No backbone weights were updated.

## Reproduction

Run from this directory with the existing Python/NumPy environment.

```sh
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python unknown_partner.py | cmp unknown-partner.json -
python mixture_partner.py | cmp mixture-partner.json -
```

[Initial protocol](unknown-partner-protocol.md) · [Follow-up protocol](mixture-partner-protocol.md) · [Preparation log](unknown-partner-preparation.md) · [Original first run](first-unknown-partner.json) · [Follow-up outputs](mixture-partner.json)
