#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: scripts/run_raceloom_progress.sh MODEL_PATH PROPERTIES_PATH --depth N --strategy S

Docker-backed single RaceLoom run. RaceLoom is distributed separately from this
repository; obtain the image first (Zenodo record 16884345, see
scripts/setup_raceloom_artifact.sh), then:

  export RACELOOM_IMAGE=raceloom:latest
  bash scripts/run_one_pair.sh BENCH_DIR DEPTH OUT_DIR

Environment:
  RACELOOM_IMAGE    required: local RaceLoom Docker image (e.g. raceloom:latest)
  RACELOOM_WORKDIR  optional: image directory containing main.py (default /raceloom)
  DOCKER_PLATFORM   optional: forwarded as `docker run --platform` when set
  RACELOOM_OUTPUT_DIR
                    optional: existing host directory bind-mounted to
                    <workdir>/output (default /raceloom/output) so RaceLoom's
                    run_* artifact directories persist on the host. It must
                    already exist and must lie outside this repository;
                    relative paths resolve against the current directory.
                    When unset, outputs stay container-internal (previous
                    behavior).
EOF
}

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 2
}

[ "$#" -ge 1 ] || { usage; exit 2; }

MODEL=""
PROPS=""
DEPTH=""
STRATEGY=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --depth)
      [ "$#" -ge 2 ] || die "--depth requires a value"
      DEPTH="$2"
      shift 2
      ;;
    --depth=*)
      DEPTH="${1#--depth=}"
      shift
      ;;
    --strategy)
      [ "$#" -ge 2 ] || die "--strategy requires a value"
      STRATEGY="$2"
      shift 2
      ;;
    --strategy=*)
      STRATEGY="${1#--strategy=}"
      shift
      ;;
    -*)
      printf 'ERROR: unknown option: %s\n\n' "$1" >&2
      usage
      exit 2
      ;;
    *)
      if [ -z "$MODEL" ]; then
        MODEL="$1"
      elif [ -z "$PROPS" ]; then
        PROPS="$1"
      else
        printf 'ERROR: unexpected extra argument: %s\n\n' "$1" >&2
        usage
        exit 2
      fi
      shift
      ;;
  esac
done

[ -n "$MODEL" ] || { printf 'ERROR: missing MODEL_PATH argument\n\n' >&2; usage; exit 2; }
[ -n "$PROPS" ] || { printf 'ERROR: missing PROPERTIES_PATH argument\n\n' >&2; usage; exit 2; }
[ -n "$DEPTH" ] || die "--depth is required (e.g. --depth 4)"
[ -n "$STRATEGY" ] || die "--strategy is required (e.g. --strategy bfs)"

case "$DEPTH" in
  ''|*[!0-9]*) die "--depth must be a non-negative integer, got: $DEPTH" ;;
esac

[ -f "$MODEL" ] || die "model file not found: $MODEL"
[ -r "$MODEL" ] || die "model file not readable: $MODEL"
[ -f "$PROPS" ] || die "properties file not found: $PROPS"
[ -r "$PROPS" ] || die "properties file not readable: $PROPS"

abs_path() {
  (cd "$(dirname "$1")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$1")")
}

MODEL_ABS="$(abs_path "$MODEL")"
PROPS_ABS="$(abs_path "$PROPS")"

command -v docker >/dev/null 2>&1 || die "docker executable not found in PATH; install/start Docker and retry"
[ -n "${RACELOOM_IMAGE:-}" ] || die "RACELOOM_IMAGE is not set. RaceLoom is distributed separately; obtain the image (Zenodo record 16884345, see scripts/setup_raceloom_artifact.sh) and export RACELOOM_IMAGE=<image>:<tag>"

docker image inspect "$RACELOOM_IMAGE" >/dev/null 2>&1 || die "RACELOOM_IMAGE='$RACELOOM_IMAGE' not found in local Docker images; load or build the RaceLoom image first (see scripts/setup_raceloom_artifact.sh)"

WORKDIR="${RACELOOM_WORKDIR:-/raceloom}"

# Optional persistent artifact output: bind-mount a host directory over the
# container-internal output directory ($WORKDIR/output) so RaceLoom's run_*
# result directories survive container exit. RaceLoom creates a fresh,
# timestamped run_* subdirectory per run; existing contents are never removed.
OUT_ABS=""
if [ "${RACELOOM_OUTPUT_DIR+x}" = x ]; then
  [ -n "$RACELOOM_OUTPUT_DIR" ] || die "RACELOOM_OUTPUT_DIR is set but empty; unset it to keep outputs container-internal, or set it to an existing host directory"
  case "$RACELOOM_OUTPUT_DIR" in
    -*) die "RACELOOM_OUTPUT_DIR must be a directory path, not an option-like value: $RACELOOM_OUTPUT_DIR" ;;
  esac
  OUT_ABS="$(cd -- "$RACELOOM_OUTPUT_DIR" 2>/dev/null && pwd -P)" || die "RACELOOM_OUTPUT_DIR='$RACELOOM_OUTPUT_DIR' is not an existing directory (relative paths resolve against the current directory); create it first, e.g.: mkdir -p -- \"$RACELOOM_OUTPUT_DIR\""
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
  case "$OUT_ABS" in
    "/"|"$REPO_ROOT"|"$REPO_ROOT"/*)
      die "RACELOOM_OUTPUT_DIR='$RACELOOM_OUTPUT_DIR' resolves to '$OUT_ABS', inside the benchmark repository ($REPO_ROOT); choose a host directory outside the repository"
      ;;
  esac
  if [ -n "$(ls -A "$OUT_ABS" 2>/dev/null)" ]; then
    printf 'NOTE: output directory %s is not empty; RaceLoom appends a new run_* subdirectory and existing contents are left untouched\n' "$OUT_ABS" >&2
  fi
fi

DOCKER_ARGS=(--rm)
if [ -n "${DOCKER_PLATFORM:-}" ]; then
  DOCKER_ARGS+=(--platform "$DOCKER_PLATFORM")
fi
DOCKER_ARGS+=(
  --workdir "$WORKDIR"
  --entrypoint python3
  -v "$MODEL_ABS:/raceloom-bench-input/model.json:ro"
  -v "$PROPS_ABS:/raceloom-bench-input/properties.json:ro"
)
if [ -n "$OUT_ABS" ]; then
  DOCKER_ARGS+=(-v "$OUT_ABS:$WORKDIR/output")
fi
DOCKER_ARGS+=(
  "$RACELOOM_IMAGE"
  main.py -d "$DEPTH" -s "$STRATEGY"
  /raceloom-bench-input/model.json
  /raceloom-bench-input/properties.json
)

exec docker run "${DOCKER_ARGS[@]}"
