#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <benchmark-pair-dir> <depth> <output-dir> [strategy]"
  echo
  echo "Example:"
  echo "  RACELOOM_IMAGE=<image> bash scripts/docker_run_pair.sh benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination 4 results/s2_smoke bfs"
  exit 2
fi

PAIR_DIR="$1"
DEPTH="$2"
OUT_DIR="$3"
STRATEGY="${4:-bfs}"

if [ ! -d "$PAIR_DIR/bad" ] || [ ! -d "$PAIR_DIR/control" ]; then
  echo "ERROR: benchmark pair directory must contain bad/ and control/: $PAIR_DIR"
  exit 2
fi

if [ -z "${RACELOOM_IMAGE:-}" ]; then
  echo "ERROR: RACELOOM_IMAGE is not set."
  echo
  echo "This repository does not include RaceLoom itself."
  echo "First obtain the RaceLoom Docker image from the RaceLoom artifact, then run:"
  echo
  echo "  export RACELOOM_IMAGE=<raceLoom-image>:<tag>"
  echo
  exit 2
fi

RACELOOM_CMD="${RACELOOM_CMD:-python main.py}"
RACELOOM_WORKDIR="${RACELOOM_WORKDIR:-/raceloom}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-}"

mkdir -p "$OUT_DIR"

echo "=== Docker mount preflight ==="
DOCKER_ARGS=(--rm)
if [ -n "$DOCKER_PLATFORM" ]; then
  DOCKER_ARGS+=(--platform "$DOCKER_PLATFORM")
fi

docker run "${DOCKER_ARGS[@]}" \
  -v "$PWD:/workspace/RaceLoom-Bench" \
  "$RACELOOM_IMAGE" \
  bash -lc "test -f '/workspace/RaceLoom-Bench/$PAIR_DIR/bad/model.json' && test -f '/workspace/RaceLoom-Bench/$PAIR_DIR/control/model.json'" \
  || {
    echo "ERROR: Docker could not see the benchmark files inside the mounted repository."
    echo "This can happen on macOS/Colima if the repository is cloned under /tmp or another unshared path."
    echo "Move the repository under your home directory and rerun the command."
    exit 2
  }

run_side() {
  local side="$1"
  local log="$OUT_DIR/${side}.log"

  echo "=== Running $side ==="
  echo "Benchmark: $PAIR_DIR"
  echo "Depth: $DEPTH"
  echo "Strategy: $STRATEGY"
  echo "Log: $log"
  echo

  DOCKER_ARGS=(--rm)
  if [ -n "$DOCKER_PLATFORM" ]; then
    DOCKER_ARGS+=(--platform "$DOCKER_PLATFORM")
  fi

  docker run "${DOCKER_ARGS[@]}" \
    -v "$PWD:/workspace/RaceLoom-Bench" \
    "$RACELOOM_IMAGE" \
    bash -lc "cd '$RACELOOM_WORKDIR' && $RACELOOM_CMD \
      /workspace/RaceLoom-Bench/$PAIR_DIR/$side/model.json \
      /workspace/RaceLoom-Bench/$PAIR_DIR/$side/properties.json \
      --depth '$DEPTH' \
      --strategy '$STRATEGY'" \
    | tee "$log"
}

run_side bad
run_side control

echo
echo "Wrote logs to: $OUT_DIR"
