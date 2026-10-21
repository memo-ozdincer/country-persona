# SFT Trial 2: short complete country responses — full evidence

[All experiments](../README.md)

Qwen3.5-4B, India and Brazil, complete national statements from S/PV.9214 (9 December 2022). Source-conditioned hypothetical policy application; no private bullet plan in training.

**Start with [GENERATED MODEL ANSWERS — outputs only](model-outputs.md).** The full before/after comparison also now places generated answers before the expandable full input. [What the evaluations measured](../EVALUATION_GUIDE.md).

| Same eight new-wording cases | Base | Four examples / 64 steps | Eight examples / 64 steps |
|---|---:|---:|---:|
| Required-content checks | 23/40 | 34/40 | 38/40 |
| Application + commitment checks | 7/16 | 15/16 | 15/16 |

These are dependent assistant annotations, not independently validated response-success rates. The five checks do not cover every possible unsupported claim or word-limit violation. Original fidelity observations and regressions remain visible.

1. **[All eight before/after comparisons](comparison.md)** — complete base, four-example and eight-example answers, exact full prompts, grades and errors (24 answers).
2. **[All eight complete SFT conversations](training.md)** — full system/user/assistant targets, including both source statements.
3. **[Training trajectories](training-metrics.md)** — configurations, losses, all 144 recorded step metrics and gradient checks.
4. **[Early ten-case evaluation](early-fits.md)** — first base, identical matched baseline rerun, 16-step and 64-step fits (40 answers).
5. **[Expanded exact and checked-plan controls](controls.md)** — all remaining controls (18 answers).
6. **[Literal-mechanism wording diagnosis](wording-diagnosis.md)** — follow-up qualifying the active/proactive ambiguity (12 answers; no new training).
7. **[Complete sources and rubric](sources-and-rubric.md)**.

All **94** saved generation records are included. They include a repeated baseline and are not 94 independent cases. The three fits started fresh: 16 + 64 + 64 = **144 updates**. Intermediate answers and adapters at every training step were not saved; none are reconstructed here.

**Offline version:** [download the complete HTML viewer](viewer.html?raw=true), then open it locally. GitHub renders the Markdown pages above directly. The HTML embeds full JSON, original token records, reviews, logs, source files and archived code, with download buttons; GitHub does not execute it inside a repository page.

[Original dated report](../../AURORA_MINIMAL_COUNTRY_20261005.md) · [Original HTML verification](export-verification.json) · [Fresh stored-evidence CPU replay](replay.json) · [GitHub export integrity receipt](../github-export-verification.json)
