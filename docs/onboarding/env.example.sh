# Set an absolute scratch directory you own before sourcing this template.
: "${PERSONA_SCRATCH_ROOT:?Set PERSONA_SCRATCH_ROOT to your own scratch directory}"
export HF_HOME="$PERSONA_SCRATCH_ROOT/cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export TORCH_HOME="$PERSONA_SCRATCH_ROOT/cache/torch"
export XDG_CACHE_HOME="$PERSONA_SCRATCH_ROOT/cache"
export UV_CACHE_DIR="$PERSONA_SCRATCH_ROOT/cache/uv"
export TMPDIR="$PERSONA_SCRATCH_ROOT/tmp"
mkdir -p -- "$HF_HOME" "$TORCH_HOME" "$TMPDIR"
# Set HF_TOKEN_PATH separately to your own private credential file when needed.
# Never print, commit, or pass the credential value on a command line.
