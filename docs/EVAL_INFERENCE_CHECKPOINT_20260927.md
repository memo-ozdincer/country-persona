# Inference instrumentation checkpoint

**Later update, 27 September:** [The pinned-model probe and 30-output comparison have completed](EVAL_BASELINE_RESULTS_20260927.md). The first attempt exposed a generation-default override, now fixed with 56 passing checks and actual GPU validation. [Job 996664](TRILLIUM_WORKFLOW.md) holds one H100 on `def-zhijing` for three hours with `sleep infinity`; experiments are separate steps. The v5 payload supersedes v3 for experiments. This replaces the authentication blocker and 20-minute one-shot boundary below. **The remainder of this document is the historical pre-GPU checkpoint; its zero-output counts describe that earlier point.**

27 September 2026. Continues the [two-event evaluation checkpoint](EVAL_PILOT_CHECKPOINT_20260927.md). **The eight-output probe now has an instrumented runner and a locally staged job payload.** Fifty-five targeted checks pass. All eight frozen prompts also ran through a tiny random Qwen3 on CPU, preserving 17,124 input tokens and generating 32 diagnostic tokens under a four-token test cap.

Those random-weight outputs test software only. There are still **zero new pretrained Qwen3-8B generations, zero new training runs and zero independent human ratings** in this evaluation pilot. CPU timings are not a GPU throughput estimate. Trillium again rejected SSH authentication; no job was submitted by this work.

## What this checkpoint establishes

| Check | Evidence | What remains unknown |
|---|---|---|
| Complete inputs | Every selected prompt traversed the real Qwen3 generation API with the locked tokenizer, including the 5,033-token maximum. Stored input IDs match the full preflight IDs. | Memory/performance of the actual 8B checkpoint on CUDA |
| Real probability extraction | A unit test compares generation's first-step logits with a separate direct forward pass. The runner saves canonical Y/N/A logits, their normalizer, conditional probabilities and legal-label mass. | The real model's confidence and decision quality |
| Conditional confidence | A controlled distribution assigns 90% to an invalid token and only 8% to Y/N/A combined. The scorer retains that 8% even though the conditional distribution sums to one. | Empirical calibration, which requires substantially more actual outcomes |
| Stopping | A controlled Qwen3 edge case emits the second EOS ID. The default stops after one token; the legacy setting continues to its cap. Both traces expose the omitted token. | Whether this mechanism contributed to the earlier trained adapter's repetition |
| EOS-only comparison | Preflight confirms identical input-token digests and only one changed generation field between default and legacy runs: `eos_token_id`. | Actual checkpoint replay, including the earlier adapter where appropriate |
| Snapshot identity | Before production loading, the runner rehashes current weights/config/tokenizer files against the existing pinned-revision receipt and the separate tokenizer lock. A corruption test rejects changed bytes despite an old successful receipt. | Current Trillium files cannot be inspected until authentication works |
| Run integrity | Cases and outputs retain hashes, raw token IDs, decoded text with/without special tokens, per-step top tokens/EOS scores, stop reasons and timing. Partial failures are marked; existing run directories cannot be overwritten. | Scheduler termination must still be checked with the actual job handle, not inferred from a stale `running` file |
| Isolated handoff | A 16-file, roughly 16 MB payload reproduces the repository's preflight from its own directory. It contains prompt inputs, code and tokenizer/config files; gold references are unnecessary for inference. | `sbatch --test-only`, GPU loading and execution |

The complete result is in [inference validation](../reports/eval-pilot-20260927/inference-validation.json), with a separate [CPU infrastructure receipt](../reports/eval-pilot-20260927/cpu-inference-smoke.json). The [original 43-check receipt](../reports/eval-pilot-20260927/validation.json) remains unchanged as a source/rubric checkpoint; the current combined count is 55, including 12 new inference tests.

## Precisely what the probability means

For action questions, the reported distribution is over the **first completion token**, conditional on that token being the canonical single-token Y, N or A. It is not the probability of the entire answer plus EOS and does not marginalize over alternative whitespace or verbal forms. Written confidence is never converted to a probability.

Keep three separate observations: the normalized Y/N/A distribution, the raw probability mass assigned to those three tokens, and whether the unconstrained generated answer obeys the requested one-character format. High conditional confidence can coexist with almost all probability mass lying outside the legal labels. An output that starts correctly and then adds prose can still fail the strict output contract.

The diagnostic uses greedy decoding, neutral penalties and the model's EOS list `[151645, 151643]`. The legacy comparison uses the tokenizer's single EOS `151645`. Full effective settings are recorded. These are explicitly declared diagnostic settings, not a claim that greedy generation is the best policy-writing decoder.

## Run boundary

The prepared batch script requests **one GPU, at most 20 minutes**: at most one-third of a requested GPU-hour. That is a resource ceiling, not an expected runtime or an accepted scheduler reservation. The primary [SciNet machine description](https://scinethpc.ca/trillium/) identifies H100 80 GB GPUs; acceptance of this particular resource request still requires scheduler validation. The official scheduling wiki was unavailable to the web tool during this check.

The job performs exactly one eight-case base-model inference run. It rechecks the pinned local snapshot and records verification/loading time separately from generation/trace time. It does not invoke the earlier training pipeline, download model weights, or automatically expand into subsequent experiments. The optional adapter and legacy-EOS CLI paths are available for separately bounded replays; the prepared job selects neither.

Current isolated payload: `runs/eval-probe-staging-20260927-v2/`. Its [tracked manifest](../reports/eval-pilot-20260927/inference-staging.json) pins every shipped file. The earlier v1 staging directory is superseded after a diagnostic shell-line correction; no cluster job used it.

After authentication is restored, stage this payload into a fresh private scratch directory, verify its hashes there, run tokenizer preflight and `sbatch --test-only`, then submit the single job and retain its ID. Inspect the resulting eight answers and traces before enlarging the run. The total objective remains the [full checkpoint plan](RESEARCH_CHECKPOINT_PLAN.md), not merely passing this software check.

## Commands

Local tokenizer-only preflight, with a fresh output directory:

```bash
.venv/bin/python scripts/run_eval_probe.py \
  --pack data/prepared/eval-pilot-20260927/probe-v1 \
  --preflight-only --output reports/eval-pilot-20260927/preflight-fresh
```

Local infrastructure test, explicitly random weights:

```bash
.venv/bin/python scripts/cpu_inference_smoke.py \
  --output runs/eval-infrastructure-fresh \
  --report reports/eval-pilot-20260927/cpu-inference-smoke-fresh.json
```

Reproduce the frozen subset or payload in fresh directories:

```bash
.venv/bin/python scripts/select_eval_probe.py \
  --pack data/prepared/eval-pilot-20260927/two-event-v1 \
  --output data/prepared/eval-pilot-20260927/probe-rebuild
.venv/bin/python scripts/stage_eval_probe.py --output runs/eval-probe-staging-fresh
```

On Trillium, from the staged directory after environment/scheduler checks:

```bash
sbatch --test-only scripts/trillium_eval_probe.sbatch
sbatch --parsable scripts/trillium_eval_probe.sbatch
```

The second command submits work; neither command has been run in this checkpoint. Keep the returned job ID as the authority for subsequent monitoring. A scheduler timeout or temporary inability to poll is not a reason to start a duplicate run.

Independent rubric calibration remains a parallel dependency. A request has been made to arrange two reviewers or have the user perform the first rating. The [blinded deck](../data/review/eval-pilot-20260927/calibration-v1/review-deck.md) and blank template are ready; authored fixture expectations must not be relabeled as human agreement.
