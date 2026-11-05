#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: scripts/run_one_pair.sh BENCH_DIR DEPTH OUT_DIR"
  exit 1
fi

BENCH="$1"
DEPTH="$2"
OUT="$3"

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 2
}

mkdir -p "$OUT"

# Optional persistent artifact isolation: when RACELOOM_OUTPUT_DIR is set, it
# names a base directory and each side is forwarded its own child directory
# (<base>/bad, <base>/control) through the same variable, so faulty and control
# artifacts never share a directory. When unset, behavior is unchanged and no
# output mount is introduced.
OUT_BASE=""
if [ "${RACELOOM_OUTPUT_DIR+x}" = x ]; then
  [ -n "$RACELOOM_OUTPUT_DIR" ] || die "RACELOOM_OUTPUT_DIR is set but empty; unset it to keep outputs container-internal, or set it to an existing base directory outside this repository"
  case "$RACELOOM_OUTPUT_DIR" in
    -*) die "RACELOOM_OUTPUT_DIR must be a directory path, not an option-like value: $RACELOOM_OUTPUT_DIR" ;;
  esac
  OUT_BASE="$(cd -- "$RACELOOM_OUTPUT_DIR" 2>/dev/null && pwd -P)" || die "RACELOOM_OUTPUT_DIR='$RACELOOM_OUTPUT_DIR' is not an existing directory (relative paths resolve against the current directory); create it first, e.g.: mkdir -p -- \"$RACELOOM_OUTPUT_DIR\""
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
  case "$OUT_BASE" in
    "/"|"$REPO_ROOT"|"$REPO_ROOT"/*)
      die "RACELOOM_OUTPUT_DIR='$RACELOOM_OUTPUT_DIR' resolves to '$OUT_BASE', inside the benchmark repository ($REPO_ROOT); choose a host directory outside the repository"
      ;;
  esac
  BAD_DIR="$OUT_BASE/bad"
  CONTROL_DIR="$OUT_BASE/control"
  for PAIR_SIDE_DIR in "$BAD_DIR" "$CONTROL_DIR"; do
    if [ -e "$PAIR_SIDE_DIR" ] || [ -L "$PAIR_SIDE_DIR" ]; then
      die "side artifact directory already exists: $PAIR_SIDE_DIR; refusing to risk mixing with prior evidence; choose a fresh base directory"
    fi
  done
  mkdir "$BAD_DIR" || die "cannot create side artifact directory: $BAD_DIR"
  if ! mkdir "$CONTROL_DIR"; then
    rmdir "$BAD_DIR" 2>/dev/null || true
    die "cannot create side artifact directory: $CONTROL_DIR"
  fi
fi

run_side () {
  SIDE="$1"

  if [ -n "$OUT_BASE" ]; then
    export RACELOOM_OUTPUT_DIR="$OUT_BASE/$SIDE"
  fi

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

  if [ -n "$OUT_BASE" ]; then
    unset RACELOOM_OUTPUT_DIR
  fi
}

run_side bad
run_side control
