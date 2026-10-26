#!/bin/bash
#SBATCH --account=def-zhijing_gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=100G
#SBATCH --output=/scratch/agokrani/unscb-qwen-eval/runs/slurm-%x-%j.out
# Usage: sbatch --job-name=NAME --gpus-per-node=h100:N --time=HH:MM:SS scripts/rorqual_unsc_bench_eval.sbatch \
#          HF_NAME MODEL_NAME RUN_DIR TP [extra scripts/run_unsc_bench_vllm_eval.py args, e.g. --limit 4]
# Submit from inside the country-persona checkout.
set -euo pipefail
HF_NAME=$1; MODEL_NAME=$2; RUN_DIR=$3; TP=$4; shift 4

module load StdEnv/2023 python/3.12 gcc cuda/12.9 opencv/4.13.0 arrow
export CUDA_HOME=$EBROOTCUDA FLASHINFER_WORKSPACE_BASE=/scratch/agokrani/unscb-qwen-eval/cache
source /scratch/agokrani/unscb-qwen-eval/env/vllm/bin/activate

S=/scratch/agokrani/unscb-qwen-eval
export HF_HOME=$S/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_CACHE_ROOT=$S/cache/vllm XDG_CACHE_HOME=$S/cache TRITON_CACHE_DIR=$S/cache/triton
export TORCHINDUCTOR_CACHE_DIR=$S/cache/inductor VLLM_NO_USAGE_STATS=1

mkdir -p "$RUN_DIR"
{ echo "job=$SLURM_JOB_ID host=$(hostname) start=$(date -Is)";
  nvidia-smi --query-gpu=name,uuid,memory.total --format=csv,noheader;
  echo "cmd=python scripts/run_unsc_bench_vllm_eval.py --hf-name $HF_NAME --model-name $MODEL_NAME --out $RUN_DIR --tp $TP $*"; } \
  > "$RUN_DIR/launch_${MODEL_NAME}.txt"

cd "$(git -C "$SLURM_SUBMIT_DIR" rev-parse --show-toplevel)"
python scripts/run_unsc_bench_vllm_eval.py --hf-name "$HF_NAME" --model-name "$MODEL_NAME" --out "$RUN_DIR" \
  --tp "$TP" --max-model-len 32768 "$@"
echo "end=$(date -Is)" >> "$RUN_DIR/launch_${MODEL_NAME}.txt"
