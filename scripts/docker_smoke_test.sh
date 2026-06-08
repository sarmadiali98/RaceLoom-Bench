#!/usr/bin/env bash
set -euo pipefail

# Fast artifact-review smoke test.
#
# This runs a small B2 route-mapping benchmark pair:
#   faulty  -> expected harmful races > 0
#   control -> expected harmful races = 0
#
# Expected exact result at depth 4 / bfs:
#   generated traces: 8
#   faulty harmful races: 1
#   control harmful races: 0

PAIR="benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta"
OUT="results/smoke_b2_route_mapping"

bash scripts/docker_run_pair.sh "$PAIR" 4 "$OUT" bfs

python3 scripts/check_pair_result.py \
  --bad-log "$OUT/bad.log" \
  --control-log "$OUT/control.log" \
  --expected-traces 8 \
  --expected-bad-harmful 1 \
  --expected-control-harmful 0
