# Learn when a second answer order is worth its cost

A learned reread policy improves net score when the first order is randomized. The fixed canonical order remains better on this docket. The trained policy uses the first observed logit margin, its display order, the late delivery rate and the reread price. It chooses whether to keep the original answer or pay for the reversed-order call and use the earlier paired decoder. [Frozen plan](plan.json) · [Protocol](protocol.md)

The six-coefficient head fits shared documentary reward minus read fees for 160 exact CPU updates using the eight original text observations. Neither stress form supplies fitting observations. The stress set still contains variants of the same two original statements. The model and renderer remain frozen. We cross two stress forms, four rates, three priors, and four hypothetical prices. Reads at the lost-receipt branch are disabled because the final relation requires the earlier source. [Training traces and all scenes](results.json)

| Policy | Released points | Extra calls per episode | Net points |
| --- | ---: | ---: | ---: |
| First order randomized, keep its answer | 52.19563 | 0 | 52.19563 |
| Always ask again when the card arrives | 53.49500 | 0.65000 | 51.13875 |
| Fitted confidence threshold | 52.19563 | 0.18789 | 51.72609 |
| Fitted order-only table | 53.14910 | 0.23281 | 52.66473 |
| Fitted margin and order policy | 53.17016 | 0.19766 | 52.82660 |
| Hindsight with the same randomized first order | 53.47395 | 0.07852 | 53.20129 |
| Fixed canonical order, one call | 53.49500 | 0 | 53.49500 |

The learned rule gains **0.63098 net** over keeping the randomized first answer. It wins on 35/96 conditions and loses on 37/96, with the mean improvement driven by larger wins. It beats the order-only table by 0.16188 and an equal-cost random reread by 0.55494. The latter is a diagnostic using the learned policy's observed call count in each scene. It wins 36/96 and ties 60/96 at that matched cost. Under a forced reversed first order, the learned rule gains 1.26938 over keeping the first answer. With canonical first, the rereads only add cost. [Count-matched audit](audit.json)

The fixed canonical order is exact on these observations, so this study shows a mitigation under order variation. The second-call price is a hypothetical fee in documentary points. The results use frozen logit archives, a source-bound renderer, and one exposed UN docket. They provide no estimate of broader order robustness, real-world inference costs, or writing quality.

## Reproduce

```sh
set -o pipefail
python3 -B optional.py plan | cmp plan.json -
python3 -B optional.py run | cmp results.json -
python3 -B audit_policy.py | cmp audit.json -
```
