# Score complete passages on Resolution 2422

Keep the same hidden-bonus evidence as the earlier letter test. Ask the Peru editor to output the exact wording of one of its two source passages, then score both candidate sequences under teacher forcing. Each sequence includes the end token. The scorer compares raw sums, per-token means, and each of those scores after subtracting the corresponding no-observation reference. It evaluates both candidate display orders separately. Serbia's fixed choice, the documentary rubric and the delivery laws stay fixed. [Protocol](protocol.md) · [Inputs and candidate sequences](plan.json)

## Result

| Decoder or rule | Mean release with receipt content | Decisions agreeing across display orders |
| --- | ---: | ---: |
| Complete-passage likelihood, total | 51.00000 | 20/20 |
| Complete-passage likelihood, per-token mean | 51.00000 | 20/20 |
| Complete-passage likelihood, centered total or mean | 50.47750 | 10/20 |
| Same-input standalone and lexical rules | 51.00000 | 20/20 |
| Earlier raw letter readout | 50.67352 | — |
| Known-checklist ceiling | 51.30125 | — |

Both raw passage scores select the standalone option on all 40 requests. Centering changes the decision but loses to standalone in seven of eight content scenes and ties in one. Its canonical and reversed scores are 50.12625 and 50.82875, respectively. Word count normalization makes no action changes on these passages, before or after centering. Replacing an arbitrary label therefore fixes the strong label preference on this archive while leaving no detectable benefit from the receipt text. [Per-token scores and selected actions](verified.json) · [Matched reward replay](scores.json)

The experiment scores 80 complete sequences, 1,240 candidate tokens and 27,776 prompt tokens across sequence evaluations. It uses Qwen3.5-4B on NVIDIA RTX PRO 6000 Blackwell Server Edition. The original two options are unchanged and both remain within the 64-token bound. The worker exits normally, and an independent receipt dispatcher verifies the final release expectations.

This compares response formats on one exposed docket with a modeled channel and a fixed source-bound writer. The hidden rubric still defines how useful a particular cross-speaker comparison would be. These results measure extraction of that choice from text. No free-form sentences were generated and no weights changed. [Runtime receipt](evidence/launch.json)

## Reproduce

Run from this directory in the project environment. These commands verify the archived token traces and scores.

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" collect_passages.py plan | cmp plan.json -
"$py" collect_passages.py verify | cmp verified.json -
"$py" score_passages.py | cmp scores.json -
```
