#!/bin/bash
# Invoke from an srun step on the allocated node, with the staged root as cwd.
set -euo pipefail
: "${SLURM_JOB_ID:?Run inside the retained allocation}"
module load StdEnv/2023 python/3.11 cuda/12.6
source /scratch/memoozd/persona/.venv/bin/activate
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mode="${1:?Choose health, baseline, deliberation, smoke, or fit-probe}"
case "$mode" in
  health)
    nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv
    python -m pip check
    python -c 'import torch, transformers, trl, peft, accelerate; print({"torch":torch.__version__, "cuda":torch.version.cuda, "gpus":torch.cuda.device_count(), "bf16":torch.cuda.is_bf16_supported(), "transformers":transformers.__version__, "trl":trl.__version__, "peft":peft.__version__, "accelerate":accelerate.__version__})'
    ;;
  deliberation)
    python scripts/run_deliberation_probe.py --model-path /scratch/memoozd/models/Qwen3-8B-Instruct --output "${2:?Supply a fresh output path}"
    ;;
  baseline)
    python scripts/run_eval_probe.py --pack data/prepared/eval-pilot-20260927/two-event-v1 --case-cap 30 --model-path /scratch/memoozd/models/Qwen3-8B-Instruct --output "${2:?Supply a fresh output path}"
    ;;
  smoke|fit-probe)
    python scripts/launch_training_readiness.py "$mode" --output "${2:?Supply a fresh output path}" --run
    ;;
  *) printf 'Unknown mode: %s\n' "$mode" >&2; exit 2 ;;
esac
