# UNSC-Bench vote baselines: Qwen3-4B-Instruct and Qwen3.8-27B

26 October 2026, Rorqual (Alliance Canada), NVIDIA H100 80GB HBM3. Evaluation only; no training.

## Question

How do a small and a recent open model vote as the five permanent members on UNSC-Bench, and how much do the scores move when known label errors are corrected or excluded?

## What runs

- `scripts/run_unsc_bench_vllm_eval.py` reproduces the UNSC-Bench paper's offline country-role protocol on the 469-row `UNSC-Bench-Clean` data (commit `f4d4d06`): same system/user templates, same JSON-schema instruction, temperature 1.0. Every raw generation is stored, so outputs can be re-parsed and re-scored without re-running.
- `scripts/rorqual_unsc_bench_eval.sbatch` runs it with vLLM 0.25.0 (`docs/onboarding/requirements-rorqual-vllm025.freeze.txt`). Raw outputs are checkpointed every 250 prompts and a resubmitted job resumes.
- `data/curation/unsc_bench_label_corrections_20261026.json` lists label corrections and flagged rows with their sources. `scripts/build_unsc_bench_label_variants.py` builds `original/`, `corrected/` and `excluded/` label sets from it without modifying the source data. `scripts/score_unsc_bench_label_variants.sh` scores a results directory against each set with the paper's own `compute_alignment_v2.py`.

| Run | Model | Output limit | Notes |
|---|---|---|---|
| `Qwen3-4B-Instruct` | `Qwen/Qwen3-4B-Instruct-2507` | 4,096 | The paper's "Qwen3-4B" |
| `Qwen3.8-27B-think16k` | `Qwen/Qwen3.8-27B` | 16,384 | Thinking on (template default); eager mode, 1 GPU. Deviates from the paper's 4,096 limit |

Votes are parsed from the final answer after `</think>`. The paper's first-JSON parse is stored alongside (`parsed_paper_first_json`) because thinking models can sketch the JSON template inside their reasoning.

## Label corrections (version 2026-10-26.1)

- **Verified, corrected:** S/2025/115 and S/2025/116 carry the final resolution 2774 vote (10-0-5). S/PV.9866 and the Council's special report on the 9866th meeting give 9-1-5 and 11-1-3; 20 member votes change, 9 of them P5.
- **Flagged, excluded in `excluded/`:** 25 adopted resolutions with every member coded `A`, which the scorer reads as ABSTAIN. S/RES/2580 (2021) is verified as adopted by acclamation; the other 24 are unverified.
- **Not yet labels:** an automated comparison of the 211 vetoed rows against downloaded S/PV records flagged 34 disagreements, mostly parser assignment errors at meetings with several drafts. Only the two amendments above are confirmed.
- Early drafts are raw OCR with heavy noise; models sometimes vote on legibility. Inputs are unchanged for comparability.

## Checks so far

- With the original labels, `score.sh` reproduces all 110 open-source model×country agreement rates in `UNSC-Bench-Clean/results/alignment_metrics.json` exactly.
- Smoke tests (4 resolutions × 5 countries): 4B 20/20 parsed; 27B 20/20 parsed, longest completion 9,451 tokens, no length stops. First-JSON and final-answer parses agreed on all 20.
- The 27B model hung in CUDA graph capture with tensor parallelism 2; eager mode on one GPU starts in about two minutes.

Model weights, environment, raw outputs and label sets are under `/scratch/agokrani/unscb-qwen-eval/` (scratch is purged after 60 days).

## Reproduce

```bash
export UNSC_BENCH_ROOT=/path/to/UNSC-Bench UNSC_BENCH_CLEAN_DATA=/path/to/UNSC-Bench-Clean/data
python scripts/build_unsc_bench_label_variants.py --out $SCRATCH/unscb-qwen-eval/labels
sbatch --job-name=unscb-4b --gpus-per-node=h100:1 --time=01:00:00 scripts/rorqual_unsc_bench_eval.sbatch \
  Qwen/Qwen3-4B-Instruct-2507 Qwen3-4B-Instruct $SCRATCH/unscb-qwen-eval/runs/full-20261026 1
sbatch --job-name=unscb-27b --gpus-per-node=h100:1 --time=04:00:00 scripts/rorqual_unsc_bench_eval.sbatch \
  Qwen/Qwen3.8-27B Qwen3.8-27B-think16k $SCRATCH/unscb-qwen-eval/runs/full-20261026 1 \
  --max-tokens 16384 --max-model-len 49152 --enforce-eager
scripts/score_unsc_bench_label_variants.sh $SCRATCH/unscb-qwen-eval/runs/full-20261026 $SCRATCH/unscb-qwen-eval/labels
```

The same corrections are proposed upstream in [UNSC-Bench-Clean PR #1](https://github.com/agokrani/UNSC-Bench-Clean/pull/1).

## Status

Full runs are queued on Rorqual (jobs 25196105, 25196106, 25196158) ahead of the 27 October–3 November power outage. No full-run scores yet.
