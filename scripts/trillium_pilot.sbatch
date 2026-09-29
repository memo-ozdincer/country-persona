#!/bin/bash
#SBATCH --account=def-zhijing
#SBATCH --job-name=persona-qwen3
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=h100:4
#SBATCH --cpus-per-task=24
#SBATCH --output=/scratch/memoozd/persona/cluster_logs/pilot_%j.out
set -euo pipefail
TASK_START_SECONDS=$SECONDS
# Preserve the allocation after success or failure for inspection/further steps.
# This remains the historical four-GPU training workflow, not the eval probe.
trap 'rc=$?; printf "EXPERIMENT_EXIT_CODE=%s ELAPSED_SECONDS=%s; retaining allocation until wall limit\n" "$rc" "$((SECONDS-TASK_START_SECONDS))"; sleep infinity' EXIT
module load StdEnv/2023 python/3.11 cuda/12.6
cd /scratch/memoozd/persona
source .venv/bin/activate
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export HF_HOME="$PWD/.cache/huggingface"
export PERSONA_MODEL_PATH=/scratch/memoozd/models/Qwen3-8B-Instruct
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1
mkdir -p runs reports
TASK_RUN_PREFIX="runs/trillium-${SLURM_JOB_ID}"
printf 'JOB_ID=%s HOST=%s\n' "$SLURM_JOB_ID" "$(hostname)"
nvidia-smi
python scripts/gpu_length_probe.py
python scripts/launch_experiment.py smoke --output "${TASK_RUN_PREFIX}-smoke" --run
python -m torch.distributed.run --standalone --nproc_per_node=4 --module country_persona.evaluate --cases data/prepared/eval-qwen3-v1/smoke_cases.jsonl --output "${TASK_RUN_PREFIX}-base"
python scripts/launch_experiment.py pilot --output "${TASK_RUN_PREFIX}-pilot" --run
python -m torch.distributed.run --standalone --nproc_per_node=4 --module country_persona.evaluate --cases data/prepared/eval-qwen3-v1/smoke_cases.jsonl --adapter "${TASK_RUN_PREFIX}-pilot" --output "${TASK_RUN_PREFIX}-after"
python scripts/compare_runs.py --cases data/prepared/eval-qwen3-v1/smoke_cases.jsonl --before "${TASK_RUN_PREFIX}-base" --after "${TASK_RUN_PREFIX}-after" --output "reports/trillium-${SLURM_JOB_ID}-before-after.md"
python scripts/check_controls.py --cases data/prepared/eval-qwen3-v1/smoke_cases.jsonl --run "${TASK_RUN_PREFIX}-base" --output "reports/trillium-${SLURM_JOB_ID}-base-controls.json"
python scripts/check_controls.py --cases data/prepared/eval-qwen3-v1/smoke_cases.jsonl --run "${TASK_RUN_PREFIX}-after" --output "reports/trillium-${SLURM_JOB_ID}-after-controls.json"
python scripts/estimate_compute.py --run "${TASK_RUN_PREFIX}-pilot/run.json" --output "reports/trillium-${SLURM_JOB_ID}-compute.json"
printf 'PILOT_COMPLETED\n'
