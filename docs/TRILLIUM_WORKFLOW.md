# Reusable Trillium allocations

User preference, 27 September 2026: use **`def-zhijing`** where available, ahead of `rrg-zhijing`. Keep allocations alive with **`sleep infinity`** so multiple experiments and interactive node SSH can share a reservation. Slurm's requested wall limit still applies.

The current evaluation workspace uses one H100 and 24 CPUs for up to three hours. `scripts/trillium_eval_probe.sbatch` only holds the reservation; it does not launch training or inference. Run bounded experiments as separate `srun` steps, inspect their outputs, then choose the next experiment within that same allocation. Experiment failure leaves the allocation available for debugging. Check existing jobs before submitting another allocation.

## Current reservation

- Job: **996664**, account **def-zhijing**, node **trig0042**, partition **compute**.
- Started: **2026-09-27 22:30:55 EDT**. Scheduled expiry: **2026-09-28 01:30:55 EDT**.
- Allocation submission directory: `/scratch/memoozd/persona/eval-probe-20260927-v3`.
- Current experiment directory: `/scratch/memoozd/persona/eval-probe-20260927-v5`.
- Local current payload: `runs/eval-probe-staging-20260927-v5/`; [file hashes](../reports/eval-pilot-20260927/inference-staging-v5.json).
- [Allocation receipt](../reports/eval-pilot-20260927/allocation-996664.json).

These describe a specific reservation, not a permanent node assignment. Verify its current state before reuse. The submitted job passed `sbatch --test-only`; all 17 shipped files passed hash verification on Trillium. Remote tokenizer preflight preserves all eight prompts: 17,124 input tokens, maximum 5,033, no truncation. The first v3 probe caught a generation-defaults bug and failed safely; v5 fixes it and completed all eight outputs on the same allocation. v4 added diagnostic context but was never run. See the [failure, regression test and successful replay receipt](../reports/eval-pilot-20260927/inference-defaults-regression.json).

## Reuse from the allocated node

Use a login shell for remote commands; a bare noninteractive SSH command did not put Slurm on PATH. Trillium rejects `srun` from its login host even with an existing job ID, so SSH into the allocated node first. Node SSH was verified for this reservation, along with its live `sleep infinity` process.

```bash
ssh trillium
squeue -u memoozd
ssh trig0042
cd /scratch/memoozd/persona/eval-probe-20260927-v5
srun --jobid=996664 --overlap --exact --ntasks=1 --cpus-per-task=24 --gpus=1 \
  --chdir="$PWD" --input=/dev/null \
  bash -l scripts/trillium_eval_probe.sh --output runs/CHOOSE-A-FRESH-NAME
```

The helper sets up the existing virtual environment, staged source tree, pinned local model, offline loading and the eight-case probe defaults. Arguments are forwarded to `run_eval_probe.py`; changing a pack or diagnostic setting must be a deliberate, recorded experiment. Each output directory is immutable. `--overlap` allows the experiment step to use resources also held by the sleeping batch step; it is not a reason to launch competing GPU experiments at once.

For an interactive shell with Slurm's GPU environment, run this from the allocated node:

```bash
srun --jobid=996664 --overlap --exact --ntasks=1 --cpus-per-task=24 --gpus=1 --chdir="$PWD" --pty bash -l
```

Prefer an `srun` step for experiments so Slurm sets the GPU visibility and records the step. Direct SSH is useful for inspection. The sleep process keeps the reservation alive; node access still depends on owning a live allocation.

## Future submissions

Prepare a fresh isolated payload, verify its files remotely, run tokenizer preflight and scheduler validation, then submit once and record the returned job ID. A temporary inability to poll is not a reason to submit a duplicate. The default three-hour reservation has a maximum requested cost of three GPU-hours; experiment timings and total reservation time are separate measurements.

All three repository batch scripts default to `def-zhijing` and retain their allocation with `sleep infinity`. The older `trillium_pilot.sbatch` and `posttrain.sbatch` still launch their original training workflows before retaining the node; **do not submit them to obtain the small evaluation workspace**. Their exit traps print `EXPERIMENT_EXIT_CODE`; a live sleeping job or eventual Slurm wall-time exit is not evidence that the experiment passed. The dedicated evaluation helper also logs its experiment exit code.

Reuse the node until the requested wall limit. Do not automatically cancel it after a successful probe; the user specifically requested retaining it for subsequent experiments.


## 28 September: retained deliberation allocation

Job `999389` on `def-zhijing` retained one H100 on `trig0014`, from 18:08:16 to its recorded 19:08:16 Toronto wall limit on 28 September. It used `sleep infinity`; the 42-call baseline and six-call follow-up completed as separate steps. The wall deadline has passed. At the 19:23 access check the multiplex socket was absent and a fresh SSH connection timed out, so final scheduler state/current GPU health could not be checked. The four-H100 training recipe remains unsubmitted. See [the results](DELIBERATION_BASELINE_20260928.md), [locally prepared nine-case follow-up](EVIDENCE_FORMAT_CHECKPOINT_20260928.md) and `reports/deliberation-999389-allocation.json`.

For a node shell driven through SSH/heredoc input, use `srun --input=/dev/null` so the first step does not consume subsequent shell commands. Confirm step/process termination before retrying. The isolated payload is `/scratch/memoozd/persona/research-readiness-20260928-v2`; additional diagnostics preserve the original frozen files.
