# Native chair replay of the learned Belgium dispatch

This is a paired writer test on the one exposed Resolution 2553 condition where changing the synthetic training menus changed a documentary decision. The UK opens, Germany reacts, the first UK clause has a 75% prior, and each transmitted card has independent 75% delivery probability. The fitted and fixed policies differ only in Belgium's choice of inclusion versus funding. The previous source-bound renderer assigned a 0.46875-point expected advantage to inclusion. [Protocol](protocol.md) · [Locked inputs and exact branch weights](plan.json)

The new chair uses frozen Qwen3.5-4B on NVIDIA RTX PRO 6000 Blackwell Server Edition. The test uses one aggregate deployment contrast across the enumerated delivery masks. Both systems feed the same public material and other delivered cards to the chair. Belgium's absent branches cancel exactly in the paired contrast. All 12 distinct prompts on the remaining branches share a 280-token output limit and a 175-word cap. [Launch receipt](evidence/launch.json)

## Result

The learned inclusion card improves the final record's expected lower rubric score by **0.78516 points**, before enforcing the source guard. **The expected difference in released score is zero.** The exact source-bound renderer's advantage on the same branch weights is +0.46875 points.

All 12 native briefs completed within both caps. Ten credited South Africa with setting or leading reform assistance mandates. The two public source blocks distinguish South Africa's role in leading the draft from the recipient country's role in setting reform assistance. The other two briefs, both with Belgium's note alone, preserved the written adoption and were marked uncertain for language that could imply Belgium endorsed a specific Fund mechanism or the Council's host-perspectives provision. Clearing both uncertain guards gives a paired difference between −0.23438 and +0.04688, depending on whether the inclusion brief gets full ownership credit. Clearing only one yields opposite directions. [Exact spans, branch scores and guard sensitivity](scores.json)

The 12 calls used 3,682 input and 2,079 generated tokens. The project worker exited normally. The first launch wrapper hit a broken pipe during device discovery and exited before creating a run. The successful wrapper exhausted the device query before choosing a free UUID and the runner checked it again. A score-only import collision was repaired by loading the local collector under a unique module name. No model output changed.

The case, delivery model and delegate cards were selected after the prior synthetic fit. A single assistant graded the briefs. This isolates a writer failure in one exposed condition and leaves interaction gains on unseen diplomatic records unmeasured.

## Reproduce

Use the existing Aurora runtime. The commands below verify the saved outputs and recompute the same-assistant scores without a new GPU launch.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" writer.py plan | cmp plan.json -
"$py" writer.py verify | cmp verified.json -
"$py" score.py | cmp scores.json -
```
