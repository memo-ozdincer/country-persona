# Environment setup

[Start here](README.md) · [Data and checkpoints](DATA_AND_RESTORE.md) · [Validation status](CHECKS.md)

Use separate environments for CPU code checks, Qwen3.5 training, and the older Qwen2.5 reference. Do not mix their dependencies. The historical `train`/`tokenize` extras in `pyproject.toml` target older Transformers/TRL versions; they are not the setup for the recent Qwen3.5 trials.

## 1. Read and verify saved evidence: Python only

Python 3.11 or newer, no installed project or third-party dependency:

```bash
python3 -B docs/onboarding/verify_starter.py
```

This works in a plain clone and does not import PyTorch or contact a model service.

## 2. CPU development/tests: Python 3.11 + locked research libraries

Prerequisites: Git, Bash and uv. The tested uv version is 0.10.10. Run from an isolated Git clone; put environments/caches on your own scratch storage. The helper never editable-installs the project or changes the frozen research payload.

```bash
# Choose a fresh absolute path on storage you own.
bash docs/onboarding/setup_cpu.sh /absolute/scratch/path/country-persona-cpu

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 \
  /absolute/scratch/path/country-persona-cpu/bin/python -B -m pytest -q

/absolute/scratch/path/country-persona-cpu/bin/python -B scripts/validate_source_inventory.py
/absolute/scratch/path/country-persona-cpu/bin/python -B -m compileall -q src scripts
```

If uv is not on PATH, set `UV_BIN` to its executable path before invoking the helper. The helper uses `uv.lock`/the `research-test` group, installs CPU PyTorch from its official wheel index, and exports dependencies with `--no-emit-project` so package builds cannot regenerate historical `.egg-info` files. Tests import source through the repository's configured `src` path.

Key versions: PyTorch 2.8.0+cpu, Transformers 5.17.0, TRL 1.14.1, PEFT 0.21.1, Datasets 5.0.1, Accelerate 1.15.0. [Check them](verify_environment.py) using `--profile cpu`.

Private integration checks can skip when the full frozen payload is absent. A skipped test does not validate that payload. See [the actual fresh-clone results](CHECKS.md).

## 3. Qwen3.5 GPU research: measured Aurora profile

The existing measured environment uses Linux x86_64, Python 3.12.3, PyTorch **2.8.0+cu128**, Transformers 5.17.0, TRL 1.14.1, PEFT 0.21.1, Datasets 5.0.1 and Accelerate 1.15.0. Its dependency check passes. All 75 installed distribution versions are captured in [environment-gpu-qwen35.json](environment-gpu-qwen35.json); [the remaining dependency freeze](requirements-qwen35-gpu.freeze.txt) excludes PyTorch, which is installed separately below.

```bash
uv venv --python 3.12 /absolute/scratch/path/country-persona-gpu

uv pip install --python /absolute/scratch/path/country-persona-gpu/bin/python \
  'torch==2.8.0+cu128' --index-url https://download.pytorch.org/whl/cu128

uv pip install --python /absolute/scratch/path/country-persona-gpu/bin/python \
  --no-deps --requirements docs/onboarding/requirements-qwen35-gpu.freeze.txt

uv pip check --python /absolute/scratch/path/country-persona-gpu/bin/python
/absolute/scratch/path/country-persona-gpu/bin/python -B \
  docs/onboarding/verify_environment.py --profile gpu
```

This is a captured measured environment and an explicit rebuild recipe. This onboarding task validates the existing GPU environment's dependency/version metadata, **not a fresh GPU rebuild or new CUDA execution**. It has no cross-platform portability or distributed/NCCL guarantee. PDF extraction/research acquisition and the separate Qwen2.5 reference used different environments; their historical reports retain those settings.

Existing Aurora project environment: `/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1`. Do not upgrade it in place. Use a new environment for any proposed change and compare before changing the validated runtime.

## Model weights and credentials

The pinned base is `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. Base weights are not in Git or release bundles. Obtain them separately from Hugging Face using your authorized access; pin the revision and verify the files against the run's model receipt before inference. Historical configs contain Memo's absolute paths: copy a config to a fresh run-specific file and change only the explicitly recorded local path fields. Do not overwrite a frozen config to make it fit your machine.

Set up caches with [env.example.sh](env.example.sh), after choosing your own `PERSONA_SCRATCH_ROOT`. Set `HF_TOKEN_PATH` separately to your own private credential file. No token values belong in Git, shell arguments, screenshots or onboarding logs. Repository access, cluster access and model access are separate permissions.

## Before any future GPU operation

Read [AGENTS.md](../../AGENTS.md). Aurora hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**. The runner requires zero used memory, zero utilization and no resident process before acquisition. Record host, GPU UUID, PID/job identity, process start time, command and run directory. Another medical project may use the same username: never terminate unfamiliar processes or perform account-wide cleanup. Recheck live ownership; old availability observations are not reservations.

The research goal is paused. Environment setup and CPU tests do not authorize a model run or a queued sequence of trials.
