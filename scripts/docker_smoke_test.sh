#!/usr/bin/env bash
set -euo pipefail

# Fast artifact-review smoke test for RaceLoom-Bench.
#
# Purpose: prove, in about a minute on native amd64 hardware, that Docker,
# the RaceLoom runtime image, and this repository's canonical execution
# pipeline work together on the reviewer's machine — before committing to the
# multi-hour benchmark reproduction.
#
# What it does:
#   1. preflights Docker and the RaceLoom image (RACELOOM_IMAGE or --image),
#   2. executes both sides (faulty first, then control) of the small B2
#      route-mapping smoke benchmark at depth 4 / BFS through the CANONICAL
#      pair runner (scripts/run_one_pair.sh -> scripts/run_raceloom_progress.sh),
#      the same pipeline the full reproduction uses,
#   3. persists both sides' RaceLoom run artifacts (final_stats.csv, harmful
#      traces) outside this repository,
#   4. independently checks the exact expected scientific outcome:
#        faulty  (bad):     8 generated traces, 1 harmful race, CRoute:1;BSw:2
#        control:           8 generated traces, 0 harmful races, CRoute:1;BSw:2
#
# Expected result: 8 traces / 1 harmful race on the faulty side and 8 traces /
# 0 harmful races on the control side; both sides report branch signature
# CRoute:1;BSw:2. A successful run ends with "SMOKE TEST: PASS".
#
# Output: everything is written under the smoke output root (default
# $HOME/raceloom-bench-smoke, override with --output-root or
# RACELOOM_SMOKE_OUTPUT_ROOT), in a fresh per-run directory, so previous
# evidence is never overwritten.
#
# Exit codes: 0 = smoke test passed, 1 = smoke test failed, 2 = environment or
# usage error.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT"

PAIR="benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta"
DEPTH="4"
STRATEGY="bfs"
EXPECTED_TRACES="8"
EXPECTED_BAD_HARMFUL="1"
EXPECTED_CONTROL_HARMFUL="0"
EXPECTED_BRANCHES="CRoute:1;BSw:2"

IMAGE="${RACELOOM_IMAGE:-}"
OUTPUT_ROOT="${RACELOOM_SMOKE_OUTPUT_ROOT:-$HOME/raceloom-bench-smoke}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --image)
      [ "$#" -ge 2 ] || { printf 'ERROR: --image requires a value\n' >&2; exit 2; }
      IMAGE="$2"; shift 2 ;;
    --output-root)
      [ "$#" -ge 2 ] || { printf 'ERROR: --output-root requires a value\n' >&2; exit 2; }
      OUTPUT_ROOT="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,38p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *) printf 'ERROR: unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done

fail_smoke() {
  printf '\nSMOKE TEST: FAIL\n%s\n' "$1" >&2
  exit 1
}

# --- preflight ---------------------------------------------------------------
command -v docker >/dev/null 2>&1 || { printf 'ERROR: docker executable not found in PATH; install/start Docker and retry\n' >&2; exit 2; }
docker info >/dev/null 2>&1 || { printf 'ERROR: docker daemon not accessible; start Docker and retry\n' >&2; exit 2; }
if [ -z "$IMAGE" ]; then
  printf 'ERROR: RACELOOM_IMAGE is not set. RaceLoom is distributed separately (Zenodo record 16884345).\nObtain and load it first:\n  bash scripts/setup_raceloom_artifact.sh\n  export RACELOOM_IMAGE=raceloom:latest\nthen rerun this smoke test.\n' >&2
  exit 2
fi
docker image inspect "$IMAGE" >/dev/null 2>&1 || { printf "ERROR: RACELOOM_IMAGE='%s' not found in local Docker images; run scripts/setup_raceloom_artifact.sh first\n" "$IMAGE" >&2; exit 2; }
IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
IMAGE_ARCH="$(docker image inspect --format '{{.Architecture}}' "$IMAGE" 2>/dev/null || printf 'unknown')"

[ -f "$PAIR/bad/model.json" ] && [ -f "$PAIR/control/model.json" ] \
  || { printf 'ERROR: smoke benchmark inputs not found under %s\n' "$PAIR" >&2; exit 2; }

# --- output location ---------------------------------------------------------
mkdir -p "$OUTPUT_ROOT" || { printf 'ERROR: cannot create smoke output root: %s\n' "$OUTPUT_ROOT" >&2; exit 2; }
OUTPUT_ROOT_ABS="$(cd "$OUTPUT_ROOT" && pwd -P)"
case "$OUTPUT_ROOT_ABS" in
  "$REPO_ROOT"|"$REPO_ROOT"/*)
    printf 'ERROR: smoke output root resolves inside the repository (%s); choose a directory outside the repository\n' "$OUTPUT_ROOT_ABS" >&2
    exit 2 ;;
esac
RUN_DIR="$OUTPUT_ROOT_ABS/smoke_$(date -u +%Y%m%dT%H%M%SZ)"
# Guarantee a fresh directory even when several runs start within the same
# second: append a discriminator suffix until creation succeeds.
SUFFIX=""
while [ -e "$RUN_DIR$SUFFIX" ]; do
  SUFFIX="-${RANDOM}${SUFFIX:+-$SUFFIX}"
done
RUN_DIR="$RUN_DIR$SUFFIX"
mkdir "$RUN_DIR" || { printf 'ERROR: cannot create smoke run directory: %s\n' "$RUN_DIR" >&2; exit 2; }
CONSOLE_DIR="$RUN_DIR/console"
ARTIFACTS_DIR="$RUN_DIR/artifacts"
mkdir "$CONSOLE_DIR" "$ARTIFACTS_DIR"

printf 'RaceLoom-Bench smoke test\n'
printf '  benchmark:      %s (faulty side first, then control)\n' "$PAIR"
printf '  depth/strategy: %s / %s\n' "$DEPTH" "$STRATEGY"
printf '  image:          %s (id: %s, architecture: %s)\n' "$IMAGE" "$IMAGE_ID" "$IMAGE_ARCH"
printf '  output:         %s\n\n' "$RUN_DIR"

# --- execution through the canonical pair runner -----------------------------
RC=0
RACELOOM_OUTPUT_DIR="$ARTIFACTS_DIR" bash scripts/run_one_pair.sh "$PAIR" "$DEPTH" "$CONSOLE_DIR" || RC=$?
if [ "$RC" -ne 0 ]; then
  fail_smoke "the canonical pair runner exited with status $RC; inspect the console logs under $CONSOLE_DIR"
fi

BAD_LOG="$CONSOLE_DIR/benchmarks_smoke_b2_route_mapping_smoke_T1_atlanta_bad_depth${DEPTH}.log"
CONTROL_LOG="$CONSOLE_DIR/benchmarks_smoke_b2_route_mapping_smoke_T1_atlanta_control_depth${DEPTH}.log"

# --- persistence checks ------------------------------------------------------
PERSIST_ERRORS=""
[ -s "$ARTIFACTS_DIR/bad/final_stats.csv" ] || PERSIST_ERRORS="missing or empty: artifacts/bad/final_stats.csv"
[ -s "$ARTIFACTS_DIR/control/final_stats.csv" ] || PERSIST_ERRORS="$PERSIST_ERRORS missing or empty: artifacts/control/final_stats.csv"
ls "$ARTIFACTS_DIR"/bad/run_*/harmful_traces >/dev/null 2>&1 || PERSIST_ERRORS="$PERSIST_ERRORS missing: artifacts/bad/run_*/harmful_traces (the faulty side reported a harmful race, so its traces must be preserved)"
if [ -n "$PERSIST_ERRORS" ]; then
  fail_smoke "RaceLoom run artifacts were not persisted:$PERSIST_ERRORS"
fi

# --- scientific outcome check -------------------------------------------------
if ! python3 scripts/check_pair_result.py \
  --bad-log "$BAD_LOG" \
  --control-log "$CONTROL_LOG" \
  --expected-traces "$EXPECTED_TRACES" \
  --expected-bad-harmful "$EXPECTED_BAD_HARMFUL" \
  --expected-control-harmful "$EXPECTED_CONTROL_HARMFUL" \
  --expected-branches "$EXPECTED_BRANCHES"; then
  fail_smoke "the executed smoke pair did not match the expected scientific outcome (see the FAIL details above); inspect the console logs under $CONSOLE_DIR"
fi

printf '\nPersisted evidence:\n  console logs:  %s\n  run artifacts: %s (bad/ and control/, each with final_stats.csv and run_*/ harmful-trace directories)\n' "$CONSOLE_DIR" "$ARTIFACTS_DIR"
printf '\nSMOKE TEST: PASS\n'
printf 'Docker, the RaceLoom image, and the canonical execution pipeline are working.\n'
printf 'Next steps: ARTIFACT.md (individual benchmarks, full reproduction, validation).\n'
