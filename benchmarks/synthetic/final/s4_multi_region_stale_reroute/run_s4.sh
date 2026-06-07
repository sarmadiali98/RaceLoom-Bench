#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-5}"
STRATEGY="${2:-bfs}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH="benchmarks/synthetic/final/s4_multi_region_stale_reroute"

echo "=== S4 bad: Multi-region stale reroute, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/bad/model.json" \
  "$BENCH/bad/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"

echo
echo "=== S4 control: Multi-region stale reroute, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh \
  "$BENCH/control/model.json" \
  "$BENCH/control/properties.json" \
  --depth "$DEPTH" \
  --strategy "$STRATEGY"
