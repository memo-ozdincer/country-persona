# Break the word-overlap shortcut on Resolution 2721

Frozen Qwen3.5-4B selected the correct adopted-text clause in **all four stress observations** after averaging the two label orders. The declared lexical rule got one right. The four observations are two source-faithful paraphrases, each presented with no word-overlap cue and with a cue favoring the competing clause. [Protocol](protocol.md) · [Locked requests](plan.json)

| Receipt text | Raw calls correct /4 | Paired choices correct /2 | Word overlap correct /2 |
| --- | ---: | ---: | ---: |
| No shared content tokens | 4 | 2 | 1 |
| Word overlap favors the competing clause | 3 | 2 | 0 |

The African members' wrong-overlap version still flips in the reversed-order call. Its mapped average favors the intended clause by only 0.3125 logit points. The zero-overlap African-members call in that order has an exact tie resolved in favor of A by the archived runtime. The canonical order is exact across the four observations, so the paired readout improves resilience to the alternate order while adding a second call. [All eight logits and matched inputs](verified.json) · [Mapped choices and documentary scores](scores.json)

At 75% delivery and equal first-card availability, both paired policies attain the **56.875/70** content ceiling. Arrival-only gets **50.6875**. In the wrong-overlap condition the lexical policy gets **44.5** because it selects the opposing clause in both worlds. The score incorporates simulated delivery and the authored relation weight. The final text uses the previously verified source clauses and renderer. The experiment checks one exposed docket and two underlying positions, with no weights updated and no evidence of open-ended writing quality. [Evidence receipt](evidence/launch.json)

One preflight assertion caught residual overlap from possessive punctuation in an initial version of the paraphrases. The wording was corrected before any inference. The final plan checks both no-overlap cases and the reversed direction before either set can enter the runner.

## Reproduce

Use the existing Aurora Python setup in the parent [reproduction instructions](../README.md#reproduce). From this directory:

```sh
set -o pipefail
"$py" stress.py plan | cmp plan.json -
"$py" stress.py verify | cmp verified.json -
"$py" score_stress.py | cmp scores.json -
```
