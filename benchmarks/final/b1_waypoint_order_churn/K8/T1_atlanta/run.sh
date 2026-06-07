#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/l3_waypoint_churn/K8/T1_atlanta"

echo "=== L3/T1/K8 bad: waypoint with background churn, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== L3/T1/K8 control: waypoint with background churn, depth=${DEPTH}, strategy=${STRATEGY} ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
