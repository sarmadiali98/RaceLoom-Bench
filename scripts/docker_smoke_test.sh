#!/usr/bin/env bash
set -euo pipefail

PAIR="benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination"
OUT="results/smoke_s2"

bash scripts/docker_run_pair.sh "$PAIR" 4 "$OUT" bfs

python3 scripts/check_pair_result.py \
  --bad-log "$OUT/bad.log" \
  --control-log "$OUT/control.log" \
  --expected-traces 38478 \
  --expected-bad-harmful 31 \
  --expected-control-harmful 0
