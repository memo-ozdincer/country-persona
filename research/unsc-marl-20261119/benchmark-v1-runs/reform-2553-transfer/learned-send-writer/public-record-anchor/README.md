# Preserve the public record and generate the delegation section

All 12 requests from the selected Resolution 2553 condition retain the same delivered national notes, probability weights and output token budget. Each final brief begins with the three public source blocks verbatim. Qwen3.5-4B sees only the private notes that arrived and writes the delegation section. The two sections are joined without editing either. A 75-word cap applies to new text and the original 175-word cap applies to the assembled record. A complete public-plus-verbatim comparator and the archived comparison renderer receive identical evidence for every receipt. [Protocol](protocol.md) · [Request and source lock](plan.json)

## Results

| Writer | Funding mean, Belgium delivered | Inclusion mean, Belgium delivered | Inclusion minus funding, full delivery distribution |
| --- | ---: | ---: | ---: |
| Fixed public record and native delegation section, released | 13.78125 | 25.28125 | +8.62500 |
| Fixed public record and native delegation section, lower raw | 33.04688 | 35.82813 | +2.08594 |
| Fixed public record and verbatim notes, released | 33.28125 | 34.28125 | +0.75000 |
| Fixed public record, verbatim notes and authored comparisons, released | 37.12500 | 37.75000 | +0.46875 |

Mean points are out of 70. Belgium-absent branches contribute zero to the paired difference. Their absolute scores were not evaluated. The split writer releases **7/12**, versus **2/12** for the clarification-only writer and **12/12** for the verbatim comparator. All 12 native briefs preserve the exact public record. The native body earns two definite joint items, one for the Germany–Belgium distinction on funding and management, and one for the shared UK–Germany negotiation concern. The other briefs include one invented peace agreement and four uncertain guards, including two ambiguous references to who retains Fund management. [All source spans, scores and retained records](scores.json)

Most of the native release contrast comes from the highest-weight branch. Its funding brief refers to procedural delays, while the source notes object to too little negotiating time. Clearing only that uncertain guard makes the contrast **−4.34766 to −2.44922**, depending on credit for the joint item. Across all 16 guard adjudications the native estimate ranges from **−8.46094 to +14.17969**. Clearing all four gives **−3.82031 to −0.26953**. These are sensitivity bounds for the reviewed drafts on this docket. The verbatim result derives from standalone coverage, and the authored comparison rules supply the additional documentary distinctions. [Exact branch weights and sensitivity](scores.json)

This was one exposed condition with the same-assistant source grading, authored messages, and simulated delivery. The inference-only run used Qwen3.5-4B on NVIDIA RTX PRO 6000 Blackwell Server Edition and exited normally. The public compilation protects the supplied facts, while the native section still needs attribution and comparison checks. Independent ratings and transfer to unseen dockets remain unmeasured. [Launch and runtime](evidence/launch.json) · [Native outputs and composed records](verified.json)

## Reproduce

From this directory in the existing Aurora environment. The archived text and scoring replay requires no new GPU calls.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" anchor_writer.py plan | cmp plan.json -
"$py" anchor_writer.py verify | cmp verified.json -
"$py" compare.py | cmp scores.json -
```
