#!/bin/bash
# Score a results directory with the paper's scorer (UNSC-Bench-Clean compute_alignment_v2.py)
# against each label variant built by scripts/build_unsc_bench_label_variants.py.
# Usage: scripts/score_unsc_bench_label_variants.sh RESULTS_DIR LABELS_DIR
set -euo pipefail
RESULTS=$1
LABELS=${2:?label variants directory from build_unsc_bench_label_variants.py}
module load StdEnv/2023 python/3.12 gcc opencv/4.13.0 arrow
source /scratch/agokrani/unscb-qwen-eval/env/vllm/bin/activate
cd "${UNSC_BENCH_CLEAN:-/home/agokrani/UNSC-Bench-Clean}"
for v in original corrected excluded; do
  python scripts/compute_alignment_v2.py --results-dirs "$RESULTS" \
    --vetoed-file "$LABELS/$v/vetoed_drafts.jsonl" \
    --nonvetoed-file "$LABELS/$v/nonvetoed_resolutions.jsonl" \
    --output "$RESULTS/alignment_metrics_$v.json" > "$RESULTS/score_$v.log" 2>&1
  cp "$LABELS/$v/manifest.json" "$RESULTS/labels_manifest_$v.json"
  echo "$v -> $RESULTS/alignment_metrics_$v.json"
done
