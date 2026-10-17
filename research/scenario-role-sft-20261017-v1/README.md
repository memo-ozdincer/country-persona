# Four-target scene/delegation SFT release

Read [the readiness report](../../docs/SCENARIO_ROLE_SFT_READINESS_20261017.md) for methods, limits and the next checkpoint. This entire small release is Git-tracked; the three original PDF pins refer to files preserved in the immutable v47 snapshot. Restore both Git and that snapshot. There is no new multi-GB archive.

Inspect `pack/example-*.txt` for the six complete rendered examples. The visible `[END OF MASKED PREFIX / BEGIN SUPERVISED AUTHENTIC SPEECH]` separator is an audit annotation and **never enters model input**. `train.jsonl` and `eval.jsonl` carry actual strings, token IDs, labels and source spans. `curation.json` is the manual review; `grounding.json` is the full source map; `rubric.json` has prospective criteria/guards; `fit-config.json` freezes the code/data/method. `validation/` holds the production-tokenizer preflight, deterministic rebuild proofs and final eight-step random-tiny-model CPU optimization trace/adapter. CPU artifacts are engineering evidence, not a country-persona result.

From the repository root, use this existing pinned ML interpreter:

```bash
task_python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
task_runs=/mfs1/u/memo/country-persona-research/runs
```

Read-only data preflight (choose a fresh output path):

```bash
"$task_python" scripts/run_scenario_sft.py preflight --output "$task_runs/scenario-preflight-v1"
```

The following are individual future operations, **not a batch script or queue**. Check live ownership and choose a genuinely free UUID explicitly. No GPU observation from an earlier date establishes availability.

```bash
"$task_python" scripts/run_scenario_sft.py evaluate --gpu-uuid GPU-EXPLICIT-UUID --output "$task_runs/scenario-base-sequence-v1"
```

For a matched ordinary-chat base control, use another `evaluate` operation with `--format native` and a fresh output. Each default evaluation generates only the two fit-excluded Ukraine answers. Raw answers and reference NLL are separate artifacts/measurements. To prepare a blank review:

```bash
python3 scripts/review_scenario_sft.py --run "$task_runs/scenario-base-sequence-v1" --output "$task_runs/scenario-base-review-draft.json"
```

Read all source material and full raw answers; complete the review manually. Do not submit the blank template. Validate that separate completed file into `inspection.json`:

```bash
python3 scripts/review_scenario_sft.py --run "$task_runs/scenario-base-sequence-v1" --review "$task_runs/scenario-base-review-complete.json" --output "$task_runs/scenario-base-sequence-v1/inspection.json"
```

Only if the inspected decision is `run_four_example_fit`, one separate operation can run:

```bash
"$task_python" scripts/run_scenario_sft.py fit --base-run "$task_runs/scenario-base-sequence-v1" --gpu-uuid GPU-EXPLICIT-UUID --output "$task_runs/scenario-fit128-v1"
```

After inspecting the fit trace, run `evaluate --adapter-run "$task_runs/scenario-fit128-v1"` on a freshly checked free device and fresh output. `--split train` tests all four fitting speeches; default `--split eval` tests the two unchanged Ukraine examples. Inspect each checkpoint before dependent work. No special-token fit, country expansion, multi-seed sweep or old explicit seed-only control is automatically launched.

Sources can be regenerated with `scripts/extract_scenario_sft_sources.py` under the pinned `pdf-source-audit-v1` interpreter; build tokenized examples with `scripts/build_scenario_sft_pack.py` under the ML interpreter. Both require fresh output directories and leave original source artifacts unchanged. The source and pack rebuild receipts show exact deterministic reproduction.
