# Trillium pilot

Workspace: `/scratch/memoozd/persona` (also `/home/memoozd/links/scratch/persona`). The single-node script is adapted from the user's `/home/memoozd/trillium_diag/2026-04-16_160614/tri_4gpu.sbatch`: account `def-zhijing`, four H100s, 24 CPU cores. The pilot requests a maximum of three hours and exits after the agreed first experiment instead of holding an idle allocation.

`scripts/trillium_pilot.sbatch` runs the length probe, technical smoke, fixed baseline generations, one-epoch pilot, fixed adapted generations, control scoring, answer comparison and calibrated cost report. It does not proceed to larger training recipes. Existing unrelated jobs are untouched.

The cached `/scratch/memoozd/models/Qwen2.5-7B-Instruct` may be selected with `PERSONA_MODEL_PATH` only after `scripts/verify_local_model.py` has matched its model/config/tokenizer bytes to the locked Hugging Face revision. Model files are read in place and are not modified. The batch environment is offline after staging.

CPU environment setup uses the project-local virtual environment and locked extras. Trillium's pip may choose an unnecessary source build for the `uv` executable; use a checksum-verified official Linux uv binary if necessary. The three-hour estimate excludes staging, queue time and human review.

Outputs are keyed by Slurm job ID in `runs/trillium-JOBID-*`, `reports/trillium-JOBID-*` and `cluster_logs/pilot_JOBID.out`. Copy comparison reports and measured run metadata back after completion; do not interpret the small arithmetic control set as a broad capability benchmark.
