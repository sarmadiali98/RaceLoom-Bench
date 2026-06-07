#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-5}"
STRATEGY="${2:-bfs}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH="benchmarks_synthetic/final/s1_multidomain_wrong_destination"

echo "=== S1 bad: Multidomain wrong destination, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/bad/model.json" \
  "$BENCH/bad/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"

echo
echo "=== S1 control: Multidomain wrong destination, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/control/model.json" \
  "$BENCH/control/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"
