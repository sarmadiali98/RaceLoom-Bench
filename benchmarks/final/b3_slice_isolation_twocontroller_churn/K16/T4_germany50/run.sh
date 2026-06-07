#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/l5_slice_isolation_churn/K16/T4_germany50"

echo "=== L5 T4_germany50 K16 bad ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== L5 T4_germany50 K16 control ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
