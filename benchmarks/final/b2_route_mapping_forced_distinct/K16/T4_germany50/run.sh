#!/usr/bin/env bash

set -euo pipefail

DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/l4_wrong_nexthop_churn/K16/T4_germany50"

echo "=== L4 T4_germany50 K16 bad ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== L4 T4_germany50 K16 control ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
