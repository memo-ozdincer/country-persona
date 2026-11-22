# Separate draft leadership from national ownership in the native chair

This prompt intervention replays all 12 receipt-matched inputs from the prior Resolution 2553 comparison. The only request change is a clarification in the common system prompt: South Africa led the draft, and the country receiving reform assistance has the role in setting that assistance. Both statements restate the public source packet. The underlying learned and fixed send policies, other visible clauses, masked-delivery weights and source rubric are identical. [Protocol](protocol.md) · [Frozen request pairs](plan.json) · [Original native chair](../README.md)

## Results

| Measure | Original chair | Clarified chair |
| --- | ---: | ---: |
| Draft leadership and reform authority conflated | 10/12 | 1/12 |
| Briefs clearing the full release contract | 0/12 | 2/12 |
| Inclusion minus funding, expected lower raw points | +0.78516 | +0.18750 |
| Inclusion minus funding, expected released points | 0.00000 | +7.75781 |

Eleven briefs preserve South Africa's draft role and the recipient country's assistance role. The remaining brief correctly separates them early, then wrongly assigns draft leadership to the host country at the end. The other failures include attaching a feasibility condition to the Secretary-General's management authority, inventing a Council endorsement of external oversight, and one brief reaching the token and word limits. Three source guards remain uncertain. [Authority spans](authority.json) · [Released scores and verified citations](scores.json)

Both released briefs use Belgium's inclusion card. Most of the expected +7.76 comes from one frequently reached branch with all three desks' notes. If its paired funding brief's uncertain guard is cleared, the expected gain changes to **−0.78516**. Across all eight accept/reject combinations for the three uncertain guards, the estimate ranges from **−1.53516 to +11.13281**. Clearing all three gives +1.83984. The source-bound renderer's contrast on the same receipts is +0.46875. The native gain under the main adjudication is driven largely by the release gate, with a much smaller difference in lower raw points. [Branch probabilities and exact sensitivity](scores.json)

This was a same-assistant read of 12 new Qwen3.5-4B drafts on NVIDIA RTX PRO 6000 Blackwell Server Edition. The inference job exited normally. The system prompt was tailored to an observed mistake on this exposed docket. The results establish a local repair to authority attribution. Comparative gains in final deliberation remain sensitive to grading, and unseen dockets remain unmeasured. [Launch link](evidence/launch.json) · [Native text and token verification](verified.json)

## Reproduce

Replay the archived outputs and their grades in the project runtime. No new generation is needed.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" scope_prompt.py plan | cmp plan.json -
"$py" scope_prompt.py verify | cmp verified.json -
"$py" compare.py | cmp scores.json -
```
