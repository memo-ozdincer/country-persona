#!/bin/bash
#SBATCH --account=def-zhijing
#SBATCH --job-name=persona-eval-workspace
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=24
#SBATCH --output=probe-%j.log
# This batch job holds the allocation. Experiments run as separate srun steps,
# so their success or failure cannot end the reservation. Slurm's wall limit
# still applies. Submit once and reuse its job ID for subsequent experiments.
printf 'JOB_ID=%s HOST=%s ACCOUNT=%s DIRECTORY=%s\n' \
  "$SLURM_JOB_ID" "$(hostname)" "$SLURM_JOB_ACCOUNT" "$SLURM_SUBMIT_DIR"
printf 'ALLOCATION_READY: run experiments with srun --jobid=%s --overlap --ntasks=1 --gpus=1 bash -l scripts/trillium_eval_probe.sh ...\n' "$SLURM_JOB_ID"
exec sleep infinity
