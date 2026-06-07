#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH="benchmarks_synthetic/final/s2_hierarchical_extended_wrong_destination"

echo "=== S2 bad: Hierarchical extended wrong destination, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/bad/model.json" \
  "$BENCH/bad/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"

echo
echo "=== S2 control: Hierarchical extended wrong destination, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/control/model.json" \
  "$BENCH/control/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"
