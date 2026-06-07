#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-results/final_matrix_logs}"
mkdir -p "$OUT"

run_pair () {
  BENCH="$1"
  DEPTH="$2"
  scripts/run_one_pair.sh "$BENCH" "$DEPTH" "$OUT"
}

run_pair benchmarks/final/b1_waypoint_order_churn/K8/T1_atlanta 5
run_pair benchmarks/final/b1_waypoint_order_churn/K12/T2_nobel_eu 4
run_pair benchmarks/final/b1_waypoint_order_churn/K14/T3_geant2012 4
run_pair benchmarks/final/b1_waypoint_order_churn/K16/T4_germany50 4

run_pair benchmarks/final/b2_route_mapping_forced_distinct/K8/T1_atlanta 5
run_pair benchmarks/final/b2_route_mapping_forced_distinct/K12/T2_nobel_eu 4
run_pair benchmarks/final/b2_route_mapping_forced_distinct/K14/T3_geant2012 4
run_pair benchmarks/final/b2_route_mapping_forced_distinct/K16/T4_germany50 4

run_pair benchmarks/final/b3_slice_isolation_twocontroller_churn/K8/T1_atlanta 5
run_pair benchmarks/final/b3_slice_isolation_twocontroller_churn/K12/T2_nobel_eu 4
run_pair benchmarks/final/b3_slice_isolation_twocontroller_churn/K14/T3_geant2012 4
run_pair benchmarks/final/b3_slice_isolation_twocontroller_churn/K16/T4_germany50 4

run_pair benchmarks/final/b4_failover_cleanup_churn/K8/T1_atlanta 5
run_pair benchmarks/final/b4_failover_cleanup_churn/K12/T2_nobel_eu 4
run_pair benchmarks/final/b4_failover_cleanup_churn/K14/T3_geant2012 4
run_pair benchmarks/final/b4_failover_cleanup_churn/K16/T4_germany50 4
