#!/usr/bin/env bash
# Mocked test suite for the reviewer-facing scripts:
#   - scripts/verify_environment.sh
#   - scripts/docker_smoke_test.sh
#   - scripts/check_pair_result.py (branch-signature extension)
#
# The tests copy the real scripts into temporary fake repositories and use a
# mock `docker` executable. No real Docker and no real RaceLoom execution
# happens; the tests prove orchestration, verdict, persistence-checking, and
# exit-code behavior only.
#
# Usage: bash scripts/test_reviewer_scripts.sh
# Exit codes: 0 = all tests passed, 1 = at least one test failed.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$HERE/.." && pwd -P)"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/raceloom-reviewer-script-tests.XXXXXX")"
cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0
ID=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'ok %s - %s\n' "$1" "$2"; }
fail_test() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'not ok %s - %s\n' "$1" "$2"; }
next_id() { printf '%s' "$((${1:-0} + 1))"; }

PINNED_ID="sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087"

# ---------------------------------------------------------------------------
# Mock docker executable (shared)
# ---------------------------------------------------------------------------

FAKE_BIN="$TMP_ROOT/bin"
mkdir -p "$FAKE_BIN"
cat > "$FAKE_BIN/docker" <<'MOCK'
#!/usr/bin/env bash
mode="$1"; shift
case "$mode" in
  info) [ "${DOCKER_MOCK_FAIL_INFO:-0}" = "1" ] && exit 1 || exit 0 ;;
  version)
    printf '29.1.3\n'
    exit 0 ;;
  image)
    if [ "${1:-}" = "inspect" ]; then
      shift
      fmt=""
      if [ "${1:-}" = "--format" ]; then fmt="$2"; shift 2; fi
      if [ "${DOCKER_MOCK_FAIL_IMAGE:-0}" = "1" ]; then exit 1; fi
      case "$fmt" in
        "{{.Id}}") printf '%s\n' "${DOCKER_MOCK_IMAGE_ID:-$PINNED_IMAGE_ID_FALLBACK}" ;;
        "{{.Architecture}}") printf 'amd64\n' ;;
        *) exit 0 ;;
      esac
      exit 0
    fi
    exit 1 ;;
  run)
    side="control"
    case "${RACELOOM_OUTPUT_DIR:-}" in
      */bad) side="bad" ;;
      */control) side="control" ;;
    esac
    harmful=0
    [ "$side" = "bad" ] && harmful="${DOCKER_MOCK_BAD_HARMFUL:-1}"
    if [ "${DOCKER_MOCK_SKIP_ARTIFACTS:-0}" != "1" ] && [ -n "${RACELOOM_OUTPUT_DIR:-}" ]; then
      mkdir -p "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces" "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces_raw"
      printf 'traces,harmful\n8,%s\n' "$harmful" > "$RACELOOM_OUTPUT_DIR/final_stats.csv"
      [ "$harmful" != "0" ] && printf 'mock harmful trace\n' > "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces/trace0.txt"
    fi
    cat <<STATS
========== Final Stats ==========
Network model branches: CRoute:1;BSw:2
Generated traces: 8
Harmful races found: $harmful
Total execution time: 0.001
=================================
STATS
    exit 0 ;;
  *) exit 1 ;;
esac
MOCK
chmod +x "$FAKE_BIN/docker"
export PATH="$FAKE_BIN:$PATH"
export PINNED_IMAGE_ID_FALLBACK="$PINNED_ID"

# ---------------------------------------------------------------------------
# Part A: verify_environment.sh
# ---------------------------------------------------------------------------

ENV_REPO="$TMP_ROOT/envrepo"
mkdir -p "$ENV_REPO/scripts" "$ENV_REPO/provenance"
cp "$REPO_ROOT/scripts/verify_environment.sh" "$ENV_REPO/scripts/"
printf 'dummy release-critical content\n' > "$ENV_REPO/README.md"
HASH_LINE="$(shasum -a 256 "$ENV_REPO/README.md" 2>/dev/null || sha256sum "$ENV_REPO/README.md")"
printf '%s  README.md\n' "$(printf '%s' "$HASH_LINE" | awk '{print $1}')" > "$ENV_REPO/provenance/checksums.sha256"

run_env() { # run_env <outdir> <args...>
  local out="$1"; shift
  ( cd "$ENV_REPO" && HOME="$TMP_ROOT/home" bash scripts/verify_environment.sh "$@" ) >"$out" 2>&1
}

mkdir -p "$TMP_ROOT/home"
export HOME="$TMP_ROOT/home"

OUT="$TMP_ROOT/env-ok.out"
run_env "$OUT" --image raceloom:latest
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && grep -q "verify_environment: OK" "$OUT" && grep -q "PASS docker executable" "$OUT" \
   && grep -q "PASS docker daemon reachable" "$OUT" && grep -q "PASS RaceLoom image present" "$OUT" \
   && grep -q "PASS image ID matches the pinned" "$OUT" && grep -q "PASS release checksum manifest" "$OUT"; then
  pass "$ID" "verify_environment passes a complete environment"
else
  fail_test "$ID" "verify_environment passes a complete environment (rc=$RC)"; sed 's/^/    /' "$OUT"
fi

OUT="$TMP_ROOT/env-mismatch.out"
DOCKER_MOCK_IMAGE_ID="sha256:different0000000000000000000000000000000000000000000000000000000000" run_env "$OUT" --image raceloom:latest
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "FAIL image ID mismatch" "$OUT" && grep -q "never silently accepted" "$OUT"; then
  pass "$ID" "verify_environment rejects a different image ID loudly"
else
  fail_test "$ID" "verify_environment rejects a different image ID loudly (rc=$RC)"
fi

OUT="$TMP_ROOT/env-noimage.out"
unset_env_image() { ( cd "$ENV_REPO" && env -u RACELOOM_IMAGE HOME="$TMP_ROOT/home" bash scripts/verify_environment.sh ) >"$OUT" 2>&1; }
unset_env_image
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && grep -q "WARN RACELOOM_IMAGE not set" "$OUT" && grep -q "verify_environment: OK" "$OUT"; then
  pass "$ID" "verify_environment skips image checks when no image is configured"
else
  fail_test "$ID" "verify_environment skips image checks when no image is configured (rc=$RC)"
fi

OUT="$TMP_ROOT/env-skipchecksums.out"
run_env "$OUT" --image raceloom:latest --skip-checksums
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && grep -q "checksum manifest verification skipped" "$OUT"; then
  pass "$ID" "verify_environment honors --skip-checksums"
else
  fail_test "$ID" "verify_environment honors --skip-checksums (rc=$RC)"
fi

printf 'tampered\n' >> "$ENV_REPO/README.md"
OUT="$TMP_ROOT/env-tampered.out"
run_env "$OUT" --image raceloom:latest
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "FAIL release checksum manifest" "$OUT"; then
  pass "$ID" "verify_environment detects release-critical file modifications"
else
  fail_test "$ID" "verify_environment detects release-critical file modifications (rc=$RC)"
fi
# restore the fake repo file for later parts
printf 'dummy release-critical content\n' > "$ENV_REPO/README.md"

OUT="$TMP_ROOT/env-badopt.out"
run_env "$OUT" --nonsense
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ]; then pass "$ID" "verify_environment rejects unknown options with exit 2"; else fail_test "$ID" "verify_environment rejects unknown options (rc=$RC)"; fi

OUT="$TMP_ROOT/env-nodocker.out"
# Build a docker-free PATH by symlinking every system executable except the
# container runtimes (the real /usr/bin contains docker on Ubuntu hosts).
NO_DOCKER_BIN="$TMP_ROOT/nodockerbin"
mkdir -p "$NO_DOCKER_BIN"
for SRC_DIR in /usr/bin /bin; do
  [ -d "$SRC_DIR" ] || continue
  for SRC in "$SRC_DIR"/*; do
    name="$(basename "$SRC")"
    case "$name" in docker*|podman*|nerdctl*) continue ;; esac
    [ -e "$NO_DOCKER_BIN/$name" ] || ln -s "$SRC" "$NO_DOCKER_BIN/$name"
  done
done
( cd "$ENV_REPO" && HOME="$TMP_ROOT/home" PATH="$NO_DOCKER_BIN" bash scripts/verify_environment.sh --skip-checksums ) >"$OUT" 2>&1
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "FAIL docker executable" "$OUT" && grep -q "FAILURES PRESENT" "$OUT"; then
  pass "$ID" "verify_environment reports missing Docker as a failure"
else
  fail_test "$ID" "verify_environment reports missing Docker as a failure (rc=$RC)"
fi

# ---------------------------------------------------------------------------
# Part B: docker_smoke_test.sh
# ---------------------------------------------------------------------------

SMOKE_REPO="$TMP_ROOT/smokerepo"
mkdir -p "$SMOKE_REPO/scripts" "$SMOKE_REPO/benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta/bad" "$SMOKE_REPO/benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta/control"
for SCRIPT in docker_smoke_test.sh run_one_pair.sh run_raceloom_progress.sh; do
  cp "$REPO_ROOT/scripts/$SCRIPT" "$SMOKE_REPO/scripts/"
done
cp "$REPO_ROOT/scripts/check_pair_result.py" "$SMOKE_REPO/scripts/"
for SIDE in bad control; do
  printf '{"mock":"model"}\n' > "$SMOKE_REPO/benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta/$SIDE/model.json"
  printf '{"mock":"props"}\n' > "$SMOKE_REPO/benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta/$SIDE/properties.json"
done

run_smoke() { # run_smoke <outdir> <args...>
  local out="$1"; shift
  ( cd "$SMOKE_REPO" && HOME="$TMP_ROOT/home" RACELOOM_IMAGE=raceloom:latest bash scripts/docker_smoke_test.sh "$@" ) >"$out" 2>&1
}

OUT="$TMP_ROOT/smoke-ok.out"
run_smoke "$OUT"
RC=$?
ID=$(next_id "$ID")
LATEST_RUN="$(ls -d "$TMP_ROOT/home/raceloom-bench-smoke"/smoke_* 2>/dev/null | tail -1)"
if [ "$RC" -eq 0 ] && grep -q "SMOKE TEST: PASS" "$OUT" && [ -n "$LATEST_RUN" ] \
   && [ -s "$LATEST_RUN/artifacts/bad/final_stats.csv" ] \
   && [ -s "$LATEST_RUN/artifacts/control/final_stats.csv" ] \
   && [ -s "$LATEST_RUN/console/benchmarks_smoke_b2_route_mapping_smoke_T1_atlanta_bad_depth4.log" ] \
   && [ -s "$LATEST_RUN/console/benchmarks_smoke_b2_route_mapping_smoke_T1_atlanta_control_depth4.log" ]; then
  pass "$ID" "smoke test passes end-to-end on the mock and persists both sides' artifacts"
else
  fail_test "$ID" "smoke test passes end-to-end on the mock (rc=$RC, run=$LATEST_RUN)"; sed 's/^/    /' "$OUT" | tail -20
fi

OUT="$TMP_ROOT/smoke-isolation.out"
run_smoke "$OUT"
RC=$?
ID=$(next_id "$ID")
RUN_COUNT="$(ls -d "$TMP_ROOT/home/raceloom-bench-smoke"/smoke_* 2>/dev/null | wc -l | tr -d ' ')"
if [ "$RC" -eq 0 ] && [ "$RUN_COUNT" -eq 2 ]; then
  pass "$ID" "a second smoke run creates a fresh isolated output directory"
else
  fail_test "$ID" "a second smoke run creates a fresh isolated output directory (rc=$RC, runs=$RUN_COUNT)"
fi

OUT="$TMP_ROOT/smoke-badscience.out"
DOCKER_MOCK_BAD_HARMFUL=5 run_smoke "$OUT"
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "SMOKE TEST: FAIL" "$OUT" && grep -q "expected 1 harmful races, got 5" "$OUT"; then
  pass "$ID" "smoke test fails loudly on a wrong scientific outcome"
else
  fail_test "$ID" "smoke test fails loudly on a wrong scientific outcome (rc=$RC)"
fi

OUT="$TMP_ROOT/smoke-noartifacts.out"
DOCKER_MOCK_SKIP_ARTIFACTS=1 run_smoke "$OUT"
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "SMOKE TEST: FAIL" "$OUT" && grep -q "not persisted" "$OUT"; then
  pass "$ID" "smoke test fails loudly when run artifacts are not persisted"
else
  fail_test "$ID" "smoke test fails loudly when run artifacts are not persisted (rc=$RC)"
fi

OUT="$TMP_ROOT/smoke-noimage.out"
( cd "$SMOKE_REPO" && env -u RACELOOM_IMAGE HOME="$TMP_ROOT/home" bash scripts/docker_smoke_test.sh ) >"$OUT" 2>&1
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ] && grep -q "RACELOOM_IMAGE is not set" "$OUT"; then
  pass "$ID" "smoke test exits 2 with guidance when RACELOOM_IMAGE is unset"
else
  fail_test "$ID" "smoke test exits 2 with guidance when RACELOOM_IMAGE is unset (rc=$RC)"
fi

OUT="$TMP_ROOT/smoke-missingimage.out"
DOCKER_MOCK_FAIL_IMAGE=1 run_smoke "$OUT"
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ] && grep -q "not found in local Docker images" "$OUT"; then
  pass "$ID" "smoke test exits 2 when the image is missing"
else
  fail_test "$ID" "smoke test exits 2 when the image is missing (rc=$RC)"
fi

OUT="$TMP_ROOT/smoke-inrepo.out"
run_smoke "$OUT" --output-root "$SMOKE_REPO/results"
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ] && grep -q "inside the repository" "$OUT"; then
  pass "$ID" "smoke test refuses an output root inside the repository"
else
  fail_test "$ID" "smoke test refuses an output root inside the repository (rc=$RC)"
fi

OUT="$TMP_ROOT/smoke-badopt.out"
run_smoke "$OUT" --nonsense
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ]; then pass "$ID" "smoke test rejects unknown options with exit 2"; else fail_test "$ID" "smoke test rejects unknown options (rc=$RC)"; fi

# ---------------------------------------------------------------------------
# Part C: check_pair_result.py branch-signature extension
# ---------------------------------------------------------------------------

LOGS="$TMP_ROOT/pairlogs"
mkdir -p "$LOGS"
cat > "$LOGS/bad.log" <<'LOG'
========== Final Stats ==========
Network model branches: CRoute:1;BSw:2
Generated traces: 8
Harmful races found: 1
Total execution time: 1.0
=================================
LOG
cat > "$LOGS/control.log" <<'LOG'
========== Final Stats ==========
Network model branches: BSw:2;CRoute:1
Generated traces: 8
Harmful races found: 0
Total execution time: 1.0
=================================
LOG

python3 "$REPO_ROOT/scripts/check_pair_result.py" --bad-log "$LOGS/bad.log" --control-log "$LOGS/control.log" \
  --expected-traces 8 --expected-bad-harmful 1 --expected-control-harmful 0 \
  --expected-branches "CRoute:1;BSw:2" >"$TMP_ROOT/pair-ok.out" 2>&1
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && grep -q "^PASS" "$TMP_ROOT/pair-ok.out"; then
  pass "$ID" "pair checker accepts matching signatures regardless of component order"
else
  fail_test "$ID" "pair checker accepts matching signatures regardless of component order (rc=$RC)"
fi

python3 "$REPO_ROOT/scripts/check_pair_result.py" --bad-log "$LOGS/bad.log" --control-log "$LOGS/control.log" \
  --expected-branches "CRoute:2;BSw:2" >"$TMP_ROOT/pair-wrong.out" 2>&1
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "branch signature mismatch" "$TMP_ROOT/pair-wrong.out"; then
  pass "$ID" "pair checker rejects a wrong branch signature"
else
  fail_test "$ID" "pair checker rejects a wrong branch signature (rc=$RC)"
fi

python3 "$REPO_ROOT/scripts/check_pair_result.py" --bad-log "$LOGS/bad.log" --control-log "$LOGS/control.log" \
  --expected-branches "CRoute:1;CRoute:1" >"$TMP_ROOT/pair-malformed.out" 2>&1
RC=$?
ID=$(next_id "$ID")
if [ "$RC" -eq 1 ] && grep -q "malformed --expected-branches" "$TMP_ROOT/pair-malformed.out"; then
  pass "$ID" "pair checker rejects malformed expected signatures"
else
  fail_test "$ID" "pair checker rejects malformed expected signatures (rc=$RC)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

printf '\n%s\n' "reviewer-script tests: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ] || exit 1
exit 0
