# Full SFT examples and model answers

Read these pages directly in GitHub. All answers come from preserved runs; this publication made no new model calls or training updates. Research remains paused.

**New collaborator:** [start here](../onboarding/README.md). [SFT Trials 1–7](../onboarding/SFT_TRIALS.md) describe each trial as context + input format + example-answer format, with results. [Environments](../onboarding/ENVIRONMENTS.md), [data/releases](../onboarding/DATA_AND_RESTORE.md), [verified checks](../onboarding/CHECKS.md), and [proposed next work](../onboarding/NEXT_STEPS.md) are all linked from that guide.

**Direct data download:** [private Hugging Face dataset](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data) — [access instructions](../onboarding/PRIVATE_HF_DATA.md). Source/training/evaluation files, full recorded outputs and saved adapters are browsable without Aurora access. The Hub dataset is private; GitHub currently reports public visibility, which this task did not change.

## Read the actual generated answers

- **[Short-answer SFT: all eight cases, base → four-example → eight-example outputs](minimal-country-sft-20261021/model-outputs.md)**. This page contains generated model answers with no long input sections.
- **[Meeting-context: all 14 continuation outputs and all 11 context-follow-up outputs](meeting-context-20261021/model-outputs.md)**. Includes failures and the model-produced reader map.
- **[What our evaluations measured, and what each model improved](EVALUATION_GUIDE.md)**. Per-criterion and per-task scores, plus limitations.

Training pages contain supplied supervision targets. They are labeled separately from generated model answers.

| Experiment | Start here | What it established |
|---|---|---|
| SFT Trial 2: short complete country responses | [All eight before/after comparisons](minimal-country-sft-20261021/comparison.md) | Base → four-example → eight-example: **23/40 → 34/40 → 38/40** content checks; **7/16 → 15/16 → 15/16** application/commitment checks. Same exposed source event; assistant grading. |
| SFT Trial 4: meeting context → authentic speech | [Meeting-context experiment](meeting-context-20261021/README.md) | Four authentic fitting speeches exact; both Ukraine development cases fail. Full earlier history only fit for sanctions. |
| Context attribution and reader/writer follow-up | [All eleven saved outputs](meeting-context-20261021/grounded-context.md) | Full dossier 12/18; attributed cards 15/18; cards + actual model map 18/18. One provisional strict pass; no additional training. |

The short-answer experiment and authentic-speech experiment are separate branches. Their scores use different criteria and cannot be pooled.

- [Short-answer SFT: complete index, training data, metrics, and all 94 answers](minimal-country-sft-20261021/README.md)
- [Meeting-context SFT: complete index, training sequences, all 14 answers, and the context follow-up](meeting-context-20261021/README.md)
- [Original consolidated research report](../CONSOLIDATED_RESULTS_20261019.md)
