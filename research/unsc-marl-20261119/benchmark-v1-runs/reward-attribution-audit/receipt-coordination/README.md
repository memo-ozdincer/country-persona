# Learn when to send after earlier evidence arrives

The source-preserving reward banks leave some room above the fixed standalone-credit rule. Most of the room is available to a better static plan. Seeing earlier receipts adds **0.05094** mean net points on Resolution 2475 and **0.01334** on Resolution 2686, even with an optimal planner.

Each desk can send one archived note or remain silent, paying the send fee even if delivery fails. At its turn it can see which earlier notes arrived. The future-forecast rule combines the observed receipts with the known checklist and predicts that remaining desks use their standalone send threshold. The learned rule fits four shared coefficients using the same inputs and the net terminal reward from the other event family. Each bank is replayed in all six orders, at four delivery rates and four fees. [Protocol](protocol.md) · [Frozen banks and setup](plan.json)

| Criterion | 2475, pair relation | 2686, alternative supporters | 2475, additive control |
| --- | ---: | ---: | ---: |
| Fixed standalone credit | 39.17859 | 35.20446 | 36.93750 |
| Fixed, use marginal on received notes | 39.46172 | 35.61990 | 36.93750 |
| Fixed, also forecast later notes | 39.69391 | 35.85784 | 36.93750 |
| Trained on the other family | 39.15078 | 35.32763 | 35.89688 |
| Same fit with receipt visibility removed | 39.15078 | 35.33605 | 35.89688 |
| Best static plan | 39.64297 | 35.84449 | 36.93750 |
| Best receipt-aware plan | 39.69391 | 35.85784 | 36.93750 |

Net scores subtract sends from the released final-record points. Receipt visibility pays off in 12/96 scenes on 2475 and 8/96 on 2686. The maximum gains are 0.68750 and 0.23288 points, respectively. The fixed forecast reaches the adaptive ceiling on every tested scene in both banks. On 2686 the learned policy loses slightly when receipts are added to its view. The additive control has zero information value, and the learned residual reduces its score relative to the exact standalone rule.

The adaptive and static values are checked by independent forward enumeration of 128 legal adaptive strategies per scene on the two primary banks. A separate finite-difference check on 288 scenes agrees with the exact training gradients to within 7.8e-10. [Per-order policies and scores](results.json)

## Checklist forecast errors

Hold the true document scores fixed and vary the declared credit for relations among notes from zero to double its correct value. The fixed forecast stays ahead on Resolution 2475 at all tested scales. On 2686 the fit leads only when the checklist omits relation credit entirely, by +0.13159 mean points. It loses 18 of the 96 scenes even there. Half-credit already restores the forecast rule's mean lead, +0.37765. This sensitivity changes the announced relative-value feature and leaves standalone credit, delivery, fees, and evaluation weights frozen. [Checklist shifts](shift.json)

The two historical families and the delivered notes were already exposed. The source-bound record scores and deployed checklist are authored. The task assumes immediate free access to earlier receipts, modeled delivery, and a single send decision per desk. No language model was run or updated. These results isolate how much these two score banks reward receipt-conditioned dispatch.

## Reproduce

```sh
set -o pipefail
python3 -B study.py plan | cmp plan.json -
python3 -B study.py run | cmp results.json -
python3 -B checklist_shift.py | cmp shift.json -
```
