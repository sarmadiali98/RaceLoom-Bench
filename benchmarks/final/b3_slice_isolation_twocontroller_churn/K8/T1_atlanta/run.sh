#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-5}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/l5_slice_isolation_churn/K8/T1_atlanta"

echo "=== L5 T1_atlanta K8 bad ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== L5 T1_atlanta K8 control ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
