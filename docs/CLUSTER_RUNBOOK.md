# Run one proof of concept on four H100s

Run from the repository root. The supplied snapshot and new research exports must be copied to the cluster: large files are Git-ignored and therefore do not accompany a Git clone. Minimum run payload: `data/prepared/posttraining-v1/`, `data/prepared/eval-v1/`, `configs/posttraining/`, source code/scripts, `pyproject.toml` and `uv.lock`. For full reproduction also preserve `data/raw/`, acquisition manifests and the source lock. Use your normal cluster transfer method; nothing has been uploaded by this project.

## Stage dependencies and weights before renting the training node

```bash
uv sync --locked --extra data --extra dev --extra tokenize --extra train
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
python - <<'PY'
import json
from huggingface_hub import snapshot_download
lock = json.load(open('configs/posttraining/model.lock.json'))
snapshot_download(lock['model'], revision=lock['revision'])
PY
```

No flash-attention build or bitsandbytes is required for the primary SDPA/BF16 recipe. CUDA/driver compatibility must be verified on the actual node. The pinned CPU TRL/PEFT integration passed locally; it is not a CUDA validation. Expect roughly 15GB of model weights, additional package/cache space and a small adapter per checkpoint; provision at least 50GB scratch headroom.

## First session: stop after the before/after proof of concept

Inside one 4×H100 80GB allocation:

```bash
# 1. Worst sequence fits; this probe updates disposable adapter weights and saves no model.
python scripts/gpu_length_probe.py

# 2. Three optimizer steps on the real format; inspect run.json and loss logs.
python scripts/launch_experiment.py smoke --run

# 3. Frozen base-model answers: four independent inference replicas, no tensor parallelism.
python -m torch.distributed.run --standalone --nproc_per_node=4 \
  --module country_persona.evaluate \
  --cases data/prepared/eval-v1/smoke_cases.jsonl --output runs/base-inspection

# 4. Fresh base + LoRA, 250 examples/country, one epoch. Does not resume smoke weights.
python scripts/launch_experiment.py pilot --run

# 5. Same prompts/evidence/decoding through the trained adapter.
python -m torch.distributed.run --standalone --nproc_per_node=4 \
  --module country_persona.evaluate \
  --cases data/prepared/eval-v1/smoke_cases.jsonl \
  --adapter runs/pilot-s42 --output runs/pilot-inspection

python scripts/compare_runs.py \
  --cases data/prepared/eval-v1/smoke_cases.jsonl \
  --before runs/base-inspection --after runs/pilot-inspection \
  --output reports/pilot_before_after.md

python scripts/estimate_compute.py --run runs/pilot-s42/run.json \
  --output reports/calibrated_compute.json
```

Read the new paired answer sheet after releasing the allocation. It is a transparent debugging sheet, not a blinded formal scoring interface. No sheet containing model outputs exists until generation actually runs. `compare_runs.py` rejects missing predictions and changed case hashes. `hit_output_cap` flags unfinished responses; do not score truncation as a policy change. All eight neutral controls can be checked exactly with `scripts/check_controls.py`.

`python scripts/launch_experiment.py pilot` **only prints** the command. `--run` launches it. Each invocation creates one run; it does not queue later stages. Existing output directories are rejected. `scripts/posttrain.sbatch` is a single-node template; supply your site's account/partition flags. The three-hour time limit is a reservation ceiling, not a promise that every later recipe fits it. Increase it only after calibrating.

The `research_prepared` path makes the checks performed here explicit. It preserves unresolved source-use status and absence of human adjudication; it does not fabricate approval entries. For institutionally reviewed releases, the original `persona admit` path remains available.

## Inspect and choose the next experiment

Use the milestone table in `POSTTRAINING_PLAN.md`. Choose **one** of these, starting again from the same pinned base:

```bash
python scripts/launch_experiment.py pilot-3epochs --run  # same data, longer learning curve
python scripts/launch_experiment.py balanced --run       # more data, same one-epoch schedule
```

These are alternatives to select after inspection, not instructions to run both automatically. Epoch checkpoints are retained. The evaluator accepts an epoch `checkpoint-N` directory beneath a completed run: it checks the saved trainer step and reads its parent run provenance. Evaluate that path with `--adapter` to inspect the learning curve. The final run directory also works.

For full development generation, replace `smoke_cases.jsonl` with `cases.jsonl` in the same inference commands and use fresh output directories. For formal review, randomize and blind run labels before giving outputs to reviewers; retain the hidden mapping. In `review.csv`, create a row for each case/run with an actual reviewer and completed counts/ratings, adjudicating duplicate reviews first:

```bash
python scripts/score_reviews.py --cases data/prepared/eval-v1/cases.jsonl \
  --reviews /path/to/adjudicated_reviews.csv \
  --before base --after balanced --output reports/reviewed_dev_comparison.json
```

No automatic political-fidelity score is substituted for missing review. Empty/unpaired review files fail. Positive change is desirable for fidelity and claim precision; negative change is desirable for error rates. Report missing review coverage, per-country and per-condition results, and event counts.

Only after selecting a recipe, create a separate final test evaluation pack:

```bash
python scripts/build_eval_pack.py --split test --output data/prepared/eval-test-v1
```

This uses reserved test QA and excludes development probes/controls. Test once after choices are fixed; do not use it for early stopping. The small number of German test events limits confidence.

## Reproduce CPU preparation

```bash
uv sync --locked --extra data --extra dev --extra tokenize
uv run python scripts/cache_tokenizer.py
# Choose new output directories if the delivered snapshots already exist.
uv run python -m country_persona.posttraining --output data/prepared/posttraining-rebuild
uv run pytest -q
```

The downstream run/evaluation scripts point to the delivered `posttraining-v1` snapshot intentionally; update the paths/configs together when promoting a new release. The tokenizer cache command downloads no model weights. Check `reports/posttraining_release.json`, `reports/compute_budget.json` and `reports/posttraining_validation.json` for measured inputs and verification.
