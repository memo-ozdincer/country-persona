#!/usr/bin/env bash
#SBATCH --job-name=country-persona-poc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=persona-%j.log
set -euo pipefail
# Submit from the repo: sbatch --export=ALL,RECIPE=pilot scripts/posttrain.sbatch
# Supply your site's account/partition flags to sbatch. Some sites use --gres=gpu:h100:4.
cd "${SLURM_SUBMIT_DIR:?Submit from the repository directory}"
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export HF_HOME="${HF_HOME:-$PWD/.cache/huggingface}"
exec .venv/bin/python scripts/launch_experiment.py "${RECIPE:-smoke}" --run
