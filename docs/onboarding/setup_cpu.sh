#!/usr/bin/env bash
# Build dependencies only: never editable-install from the evidence workspace.
set -euo pipefail
if [[ $# != 1 || "$1" != /* ]]; then
  printf 'Usage: bash docs/onboarding/setup_cpu.sh /absolute/scratch/path/new-cpu-env\n' >&2
  exit 2
fi
PERSONA_CPU_ENV="$1"
if [[ -e "$PERSONA_CPU_ENV" || -e "${PERSONA_CPU_ENV}.requirements.txt" ]]; then
  printf 'Choose a fresh environment destination.\n' >&2
  exit 2
fi
PERSONA_CODE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
PERSONA_UV_BIN="${UV_BIN:-uv}"
PERSONA_ENV_PARENT="$(dirname -- "$PERSONA_CPU_ENV")"
mkdir -p -- "$PERSONA_ENV_PARENT/tmp"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PERSONA_ENV_PARENT/uv-cache}"
export TMPDIR="$PERSONA_ENV_PARENT/tmp"
"$PERSONA_UV_BIN" venv --python 3.11 "$PERSONA_CPU_ENV"
"$PERSONA_UV_BIN" export --project "$PERSONA_CODE_ROOT" --locked --extra data --extra dev \
  --group research-test --prune torch --no-hashes --no-emit-project \
  --output-file "${PERSONA_CPU_ENV}.requirements.txt" >/dev/null
"$PERSONA_UV_BIN" pip install --python "$PERSONA_CPU_ENV/bin/python" 'torch==2.8.0' \
  --index-url https://download.pytorch.org/whl/cpu
"$PERSONA_UV_BIN" pip install --python "$PERSONA_CPU_ENV/bin/python" \
  --requirements "${PERSONA_CPU_ENV}.requirements.txt"
"$PERSONA_UV_BIN" pip check --python "$PERSONA_CPU_ENV/bin/python"
"$PERSONA_CPU_ENV/bin/python" -B "$PERSONA_CODE_ROOT/docs/onboarding/verify_environment.py" --profile cpu
printf 'CPU environment ready: %s\n' "$PERSONA_CPU_ENV"
