# Keep useful evidence and learn when the native writer helps

The editor and chair make different decisions. The editor selects and delivers useful source evidence. The chair decides whether to publish a verbatim record or use the archived native writer. The chair's fit uses the receipt IDs, the known verbatim score, and one observed final score per exploratory exchange. Unseen receipts default to verbatim. A native route costs a hypothetical 0.5 documentary points. [Protocol](protocol.md) · [Frozen bank and replay inputs](plan.json)

| Docket and fixed editor | Verbatim net | Always-native net | Learned composition net, 16 / 256 scores | Authored comparison |
| --- | ---: | ---: | ---: | ---: |
| 2721, source-trained | 44.50000 | 17.00000 | 44.50000 / 44.50000 | 56.87500 |
| 2721, native-reward-trained | 42.81250 | 42.31250 | 42.81250 / 42.81250 | 42.81250 |
| 2553, Belgium sends funding | 33.28125 | 13.28125 | 33.68628 / 33.93750 | 37.12500 |
| 2553, Belgium sends inclusion | 34.28125 | 24.78125 | 35.27826 / 36.60156 | 37.75000 |

Resolution 2721 uses 75% delivery and equal early-card availability. Resolution 2553 uses 75% delivery and a 75% prior for the first opening passage. The 2553 numbers are **conditional on Belgium's note arriving** because those are the archived writer inputs. The authored column has no native fee.

On 2721 the learned chair always uses the verbatim route, so it ties that fixed policy. The source-trained editor delivers supporting pairs on **56.25%** of episodes. The previous native-reward editor delivers none. Composing after delivery makes it possible to keep the evidence without triggering the observed native writer failures. The verbatim route itself earns no credit for an explicit comparison. 

On 2553, the learned gate adds native prose only on the two exact receipts that improve strict release. With 256 simulated scores it reaches its writer-choice ceiling for both editors. The gain over verbatim is **0.65625** points for funding and **2.32031** for inclusion in the shown condition. The latter uses the native path on 42.19% of Belgium-present episodes. Resolving the uncertain source grades leaves the learned policy's score unchanged, because none of those drafts is selected. [Learning curves, gate choices and all delivery conditions](results.json)

## Hold the gate fixed and change the writer

The learned 2553 gate raises inclusion net to 36.60156 with the split writer it saw during calibration. Reusing the same gate with the clarification-only writer yields 28.16406. With the original free-form writer it yields 18.88281. Both fall below verbatim at 34.28125. The exact receipt ID cannot tell the gate that the underlying writer has changed. [Writer swap and hashes](swap.json)

This experiment uses the original authored notes and archived native drafts with same-assistant grades. It measures a composition policy calibrated per receipt and per archived writer. It adds no model calls, general semantic review, or unseen event transfer. Training uses one observed output route each time. Evaluation uses exact scores from both routes.

## Reproduce

```sh
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" compose_choice.py plan | cmp plan.json -
"$py" compose_choice.py run | cmp results.json -
"$py" writer_swap.py | cmp swap.json -
```
