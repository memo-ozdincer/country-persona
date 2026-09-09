#!/usr/bin/env bash
set -euo pipefail
# Usage: NPROC_PER_NODE=4 bash scripts/train_multigpu.sh [country_persona.train arguments]
# Effective batch = NPROC_PER_NODE * --grad-accum (microbatch is one).
exec torchrun --standalone --nproc_per_node="${NPROC_PER_NODE:-4}" --module country_persona.train "$@"
