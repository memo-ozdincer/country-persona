# Select the adopted clause from the text of a received note

Frozen Qwen3.5-4B reads the two adopted clauses and a neutral relay envelope. The inputs omit numeric priorities, the relation rubric and the expected selection. Four kinds of envelope present each source position with attribution, without attribution, in an indirect paraphrase, and with a separate background cue about the competing topic. The earlier receipt is represented by the original verified note when rendering the final record. The paraphrase affects only the editor's information. [Protocol](protocol.md) · [20 locked requests](plan.json)

The two calls for each observation reverse the candidate letters and display order. The decoder averages mapped logits, and the replay records per-order choices as well as the averaged choice. An equal-budget comparison for the two-call condition is the paired arrival-only readout. The lexical rule computes Jaccard overlap over distinct lowercase tokens from the explanation and each clause, excluding the locked stop words and the separately marked background cue.

## Initial results

| Observation form | Correct individual calls /4 | Mapped decisions agreeing across orders /2 | Correct paired calls /2 | Lexical correct /2 |
| --- | ---: | ---: | ---: | ---: |
| Attributed | 3 | 1 | 2 | 2 |
| Anonymous | 4 | 2 | 2 | 2 |
| Indirect | 3 | 1 | 2 | 2 |
| Indirect with separate cue | 3 | 1 | 2 | 2 |

The paired readout attains the documentary ceiling on all 12 rate/prior combinations for each form. At equal prior and 75% delivery it gains 6.1875 points over paired arrival-only. In this particular panel the canonical order alone is also exact across all eight content observations. Averaging helps recover invariance to the alternate order, and its benefit cannot be inferred by comparing to canonical alone. Lexical matching ties every paired decision in the initial panel. The label reversal and name omissions alone therefore do not identify semantic matching. [Mapped margins and scores](scores.json)

The first plan-only attempt stopped because a generic local module name shadowed a legacy dependency. Loading the local fixture under a unique module name repaired it before any GPU launch. All 20 captured native calls used the frozen 4B checkpoint on NVIDIA RTX PRO 6000 Blackwell Server Edition. The task tests clause selection from authored source paraphrases under a simulated channel. The chair uses an authored renderer. There is no new LLM weight update, drafting-quality result, or independent unseen event-family evaluation. [Launch and checkpoint](evidence/launch.json) · [Verified logits](verified.json)

## Word-overlap follow-up

The paired decoder gets all four observations right when overlap is removed or points to the other clause. The overlap rule gets one right. The reversed order still flips one response and the averaged margin is small. [Stress cases and results](lexical-contrast/README.md)

## Reproduce

From this directory in the existing Aurora environment. The replay uses archived forward outputs.

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" decode_2721.py plan | cmp plan.json -
"$py" decode_2721.py verify | cmp verified.json -
"$py" score_decode.py | cmp scores.json -
```
