#!/bin/bash
#SBATCH --account=def-zhijing
#SBATCH --job-name=persona-ready
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=h100:4
#SBATCH --cpus-per-task=24
#SBATCH --time=01:00:00
#SBATCH --output=persona-ready-%j.log
set -euo pipefail
printf 'Retained allocation: JOB_ID=%s HOST=%s; experiments are separate steps.\n' "$SLURM_JOB_ID" "$(hostname)"
exec sleep infinity
