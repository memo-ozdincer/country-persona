# Native passage decisions after a Resolution 2553 receipt

Frozen Qwen3.5-4B makes both the later desk's receipt-conditioned
choice and Belgium's independent choice. The earlier desk is
assigned a single private claim, with a 0.75 prior for its process
passage. We use both UK–Germany orders and 0.55 or 0.95 independent
receipt probability. An actor sees its own text, the public
score and dependency table, and its assigned receipt view.
The judge uses the fixed source-bound renderer for realized
evidence. Only the content arm gets the early passage text.
[Protocol](protocol.md) · [Locked prompts and provenance](plan.json) ·
[Original Resolution 2553 docket](../README.md)

## Decoder behavior

All 48 physical calls choose the literal letter B. Swapping the
letter mapping reverses the selected card in every one of the
24 paired contexts. Averaging the two mapped logit margins
recovers a consistent response on the four scenario pairs. The
later desk chooses its process passage when it sees the earlier
process card and its other passage otherwise. In six contexts
the mapped margin is exactly zero. All four Belgium decisions
and the two UK arrival-only decisions in the mean decoder then
use the prespecified local-coverage fallback.

The two single-order decoders have mean content scores of
34.63 and 35.46, each unchanged by receipt visibility. The
agreement-only decoder falls back to local coverage on all 24
logical contexts and produces a mean of 35.76 in every arm.
The gain below belongs to the prespecified two-order decoder.
[Raw logits](evidence/calls.jsonl) · [Verified token traces and records](verified.json) ·
[Mapped margins and decisions](scores.json)

## Source-valued replay

| Later desk and receipt rate | Native content | Native arrival only | Best arrival only | Best content |
| --- | ---: | ---: | ---: | ---: |
| UK, 0.55 | 31.9711 | 31.6875 | 31.6875 | 31.9711 |
| UK, 0.95 | 41.5798 | 42.0875 | 42.0875 | 42.0875 |
| Germany, 0.55 | 31.4606 | 30.5531 | 31.3094 | 31.4606 |
| Germany, 0.95 | 41.4106 | 38.7031 | 40.9594 | 41.4106 |

The combined decoder improves its own arrival-only arm by **0.848
expected points** on average, winning three and losing one. Against
the strongest arrival-only comparator the gain is **0.095**.
The combined decoder reaches the content ceiling in three
conditions. It loses 0.508 at high UK delivery, where its automatic
switch to the process card ignores the competing inclusion bonus.
Using the exact later-desk policy with the same Belgium choice
closes that loss. Replacing Belgium alone leaves every result
the same. These swaps are exact planning diagnostics.

The earlier fixed and learned content policies average 36.3455
here. The repaired fixed policy reaches the 36.7325 content
ceiling, compared with 36.6055 for the native content policy.
The new benefit is in the model's receipt-dependent selection
under the two-order decoder. The stronger point-based planner
retains the higher absolute return.
[All 92 independently checked policy outcomes](scores.json)

The cost readout gives break-even extra forwarding charges
assuming they are incurred once per early arrival. The large
native content-versus-native-arrival margins in the Germany-later
conditions partly reflect weak native arrival decisions. Against
the strongest arrival-only rule, the positive conditions can
cover 0.516, 0.275 and 0.475 documentary points per forwarding
attempt. The high-delivery UK condition loses even at zero fee.
Across four equally weighted conditions, the common break-even
fee against the strongest arrival-only rule is about 0.126 points.
These are documentary point equivalents under a simulated cost
model. [Individual costing readouts](cost.json)

The 48 Qwen3.5-4B forwards consume 21,340 input tokens and
emit 96 constrained output tokens. Inference takes 8.06 measured
seconds on NVIDIA RTX PRO 6000 Blackwell Server Edition,
excluding checkpoint load. No optimizer updates occur. The
outcomes come from one exposed archive, authored evidence and
modeled delivery. The evaluator does not measure unrestricted
deliberation or unseen-family transfer.

## Reproduce

Use the Aurora Python setup from the
[parent run](../README.md#reproduce). From this directory:

```bash
set -o pipefail
sha256sum -c analysis.lock
sha256sum -c cost-readout.lock
"$py" live_choices.py plan | cmp plan.json -
"$py" live_choices.py verify | cmp verified.json -
"$py" score_native.py | cmp scores.json -
"$py" cost_readout.py | cmp cost.json -
```
