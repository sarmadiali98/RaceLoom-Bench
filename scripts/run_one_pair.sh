#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: scripts/run_one_pair.sh BENCH_DIR DEPTH OUT_DIR"
  exit 1
fi

BENCH="$1"
DEPTH="$2"
OUT="$3"

mkdir -p "$OUT"

run_side () {
  SIDE="$1"

  echo
  echo "################################################################################"
  echo "$BENCH $SIDE depth=$DEPTH"
  echo "################################################################################"

  scripts/run_raceloom_progress.sh \
    "$BENCH/$SIDE/model.json" \
    "$BENCH/$SIDE/properties.json" \
    --depth "$DEPTH" \
    --strategy bfs \
    2>&1 | tee "$OUT/$(echo "$BENCH" | tr '/' '_')_${SIDE}_depth${DEPTH}.log"
}

run_side bad
run_side control
