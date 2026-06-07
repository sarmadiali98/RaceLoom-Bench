#!/usr/bin/env bash
set -euo pipefail
DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/l3_waypoint_churn/K12/T2_nobel_eu"

echo "=== L3/T2_nobel_eu/K12 bad ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== L3/T2_nobel_eu/K12 control ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
