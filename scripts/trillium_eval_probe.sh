#!/bin/bash
# Run from the staged payload inside a GPU allocation. Arguments are forwarded
# to run_eval_probe.py; always supply a fresh --output directory.
set -euo pipefail
: "${SLURM_JOB_ID:?Run inside the retained Slurm allocation, using srun or node SSH}"
module load StdEnv/2023 python/3.11 cuda/12.6
source /scratch/memoozd/persona/.venv/bin/activate
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1
export HF_HOME="$PWD/.cache/huggingface"
TASK_PROBE_START_SECONDS=$SECONDS
trap 'rc=$?; printf "EXPERIMENT_EXIT_CODE=%s ELAPSED_SECONDS=%s\n" "$rc" "$((SECONDS-TASK_PROBE_START_SECONDS))"' EXIT
printf 'JOB_ID=%s STEP_ID=%s HOST=%s\n' "$SLURM_JOB_ID" "${SLURM_STEP_ID:-node-ssh}" "$(hostname)"
nvidia-smi
python scripts/run_eval_probe.py \
  --pack data/prepared/eval-pilot-20260927/probe-v1 \
  --model-path /scratch/memoozd/models/Qwen3-8B-Instruct \
  --model-receipt reports/trillium_model_verification.json \
  --eos-policy model --max-new-tokens 384 --context-budget 8192 --case-cap 8 \
  "$@"
