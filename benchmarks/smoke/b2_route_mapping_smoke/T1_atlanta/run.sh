#!/usr/bin/env bash
set -euo pipefail

DEPTH="${1:-4}"
STRATEGY="${2:-bfs}"
BENCH="benchmarks_comprehensive_topologies/b2_route_mapping_smoke/T1_atlanta"

echo "=== B2 route-mapping smoke bad ==="
~/run_raceloom_progress.sh "$BENCH/bad/model.json" "$BENCH/bad/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"

echo
echo "=== B2 route-mapping smoke control ==="
~/run_raceloom_progress.sh "$BENCH/control/model.json" "$BENCH/control/properties.json" --depth "$DEPTH" --strategy "$STRATEGY"
