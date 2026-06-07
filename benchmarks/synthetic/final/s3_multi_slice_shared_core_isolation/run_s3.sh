#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-5}"
STRATEGY="${2:-bfs}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH="benchmarks_synthetic/final/s3_multi_slice_shared_core_isolation"

echo "=== S3 bad: Multi-slice shared-core isolation, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/bad/model.json" \
  "$BENCH/bad/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"

echo
echo "=== S3 control: Multi-slice shared-core isolation, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/control/model.json" \
  "$BENCH/control/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"
