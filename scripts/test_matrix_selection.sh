#!/usr/bin/env bash
# Mocked test suite for single-configuration selection (RACELOOM_MATRIX_ONLY)
# on both canonical matrix launchers, and for full-matrix/resume interplay.
#
# The tests copy the real launchers, the real pair runner, and the real Docker
# wrapper into a temporary fake repository with minimal benchmark inputs, and
# put a mock `docker` executable on PATH. No real Docker and no real RaceLoom
# execution happens; the mock proves orchestration behavior only (selection
# filtering, rejection of invalid values, evidence layout, resume behavior,
# and exit codes), not scientific output.
#
# Usage: bash scripts/test_matrix_selection.sh
# Exit codes: 0 = all tests passed, 1 = at least one test failed.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$HERE/.." && pwd -P)"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/raceloom-selection-tests.XXXXXX")"
cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'ok %s - %s\n' "$1" "$2"; }
fail_test() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'not ok %s - %s\n' "$1" "$2"; }
next_id() { printf '%s' "$((${1:-0} + 1))"; }

# ---------------------------------------------------------------------------
# Fake repository construction
# ---------------------------------------------------------------------------

FAKE_REPO="$TMP_ROOT/repo"
mkdir -p "$FAKE_REPO/scripts" "$FAKE_REPO/benchmarks/final" "$FAKE_REPO/benchmarks/synthetic/final"

for SCRIPT in run_final_matrix.sh run_supplementary_matrix.sh run_one_pair.sh run_raceloom_progress.sh; do
  cp "$REPO_ROOT/scripts/$SCRIPT" "$FAKE_REPO/scripts/$SCRIPT" || exit 1
done

# Principal benchmark inputs: 4 families x 4 topology configs.
PRINCIPAL_BENCHES=(
  "b1_waypoint_order_churn/K8/T1_atlanta"
  "b1_waypoint_order_churn/K12/T2_nobel_eu"
  "b1_waypoint_order_churn/K14/T3_geant2012"
  "b1_waypoint_order_churn/K16/T4_germany50"
  "b2_route_mapping_forced_distinct/K8/T1_atlanta"
  "b2_route_mapping_forced_distinct/K12/T2_nobel_eu"
  "b2_route_mapping_forced_distinct/K14/T3_geant2012"
  "b2_route_mapping_forced_distinct/K16/T4_germany50"
  "b3_slice_isolation_twocontroller_churn/K8/T1_atlanta"
  "b3_slice_isolation_twocontroller_churn/K12/T2_nobel_eu"
  "b3_slice_isolation_twocontroller_churn/K14/T3_geant2012"
  "b3_slice_isolation_twocontroller_churn/K16/T4_germany50"
  "b4_failover_cleanup_churn/K8/T1_atlanta"
  "b4_failover_cleanup_churn/K12/T2_nobel_eu"
  "b4_failover_cleanup_churn/K14/T3_geant2012"
  "b4_failover_cleanup_churn/K16/T4_germany50"
)
SUPPLEMENTARY_BENCHES=(
  "s1_multidomain_wrong_destination"
  "s2_hierarchical_extended_wrong_destination"
  "s3_multi_slice_shared_core_isolation"
  "s4_multi_region_stale_reroute"
)

make_bench_inputs() {
  local bench="$1"
  mkdir -p "$FAKE_REPO/$bench/bad" "$FAKE_REPO/$bench/control"
  printf '{"mock":"model-%s"}\n' "$bench" > "$FAKE_REPO/$bench/bad/model.json"
  printf '{"mock":"props"}\n' > "$FAKE_REPO/$bench/bad/properties.json"
  printf '{"mock":"model-%s"}\n' "$bench" > "$FAKE_REPO/$bench/control/model.json"
  printf '{"mock":"props"}\n' > "$FAKE_REPO/$bench/control/properties.json"
}
for BENCH in "${PRINCIPAL_BENCHES[@]}"; do make_bench_inputs "benchmarks/final/$BENCH"; done
for BENCH in "${SUPPLEMENTARY_BENCHES[@]}"; do make_bench_inputs "benchmarks/synthetic/final/$BENCH"; done

# The launchers hash the repository state; a real (tiny) git repository is
# required for the provenance step to succeed.
git -C "$FAKE_REPO" init -q
git -C "$FAKE_REPO" -c user.email=mock@example.com -c user.name=mock add -A
git -C "$FAKE_REPO" -c user.email=mock@example.com -c user.name=mock commit -qm "mock repository"

# ---------------------------------------------------------------------------
# Mock docker executable
# ---------------------------------------------------------------------------

FAKE_BIN="$TMP_ROOT/bin"
mkdir -p "$FAKE_BIN"
MOCK_LOG="$TMP_ROOT/docker_calls.log"
: > "$MOCK_LOG"

cat > "$FAKE_BIN/docker" <<'MOCK'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$DOCKER_MOCK_LOG"
mode="$1"; shift
case "$mode" in
  info) exit 0 ;;
  version)
    # docker version --format '{{.Client.Version}}' / '{{.Server.Version}}'
    printf '29.1.3\n'
    exit 0 ;;
  image)
    if [ "${1:-}" = "inspect" ]; then
      shift
      fmt=""
      if [ "${1:-}" = "--format" ]; then fmt="$2"; shift 2; fi
      case "$fmt" in
        "{{.Id}}") printf 'sha256:mockimage0000000000000000000000000000000000000000000000000000000\n' ;;
        "{{.Architecture}}") printf 'amd64\n' ;;
        "{{.RepoDigests}}") printf '[]\n' ;;
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
    if [ -n "${RACELOOM_OUTPUT_DIR:-}" ]; then
      mkdir -p "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces" "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces_raw"
      printf 'traces,harmful\n96309,%s\n' "$([ "$side" = bad ] && printf 1 || printf 0)" \
        > "$RACELOOM_OUTPUT_DIR/final_stats.csv"
      printf 'mock harmful trace\n' > "$RACELOOM_OUTPUT_DIR/run_1/harmful_traces/trace0.txt"
    fi
    cat <<STATS
========== Final Stats ==========
Network model branches: CBg:8;BSw:10
Generated traces: 96309
Harmful races found: $([ "$side" = bad ] && printf 1 || printf 0)
Total execution time: 0.001
=================================
STATS
    exit 0 ;;
  *) exit 1 ;;
esac
MOCK
chmod +x "$FAKE_BIN/docker"

export DOCKER_MOCK_LOG="$MOCK_LOG"
export PATH="$FAKE_BIN:$PATH"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

docker_run_calls() { grep -c '^run ' "$MOCK_LOG" || true; }
reset_mock_log() { : > "$MOCK_LOG"; }

status_rows() { # status_rows <root>: number of data rows in status.tsv
  [ -f "$1/status.tsv" ] || { printf 0; return; }
  awk 'END{print NR-1}' "$1/status.tsv"
}

# ---------------------------------------------------------------------------
# Principal launcher: selection mode
# ---------------------------------------------------------------------------

ID=0

reset_mock_log
OUT1="$TMP_ROOT/out-principal-select"
mkdir -p "$OUT1"
if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUT1" \
   RACELOOM_MATRIX_ONLY=B2_K14_T3_geant2012 \
   bash "$FAKE_REPO/scripts/run_final_matrix.sh" >"$TMP_ROOT/t1.out" 2>&1; then
  RC=0
else
  RC=$?
fi
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ]; then pass "$ID" "principal selection valid ID exits 0"; else fail_test "$ID" "principal selection valid ID exits 0 (rc=$RC)"; fi

ID=$(next_id "$ID")
if [ "$(status_rows "$OUT1")" -eq 1 ]; then pass "$ID" "principal selection writes exactly one status row"; else fail_test "$ID" "principal selection writes exactly one status row (got $(status_rows "$OUT1"))"; fi

ID=$(next_id "$ID")
if [ -d "$OUT1/B2_K14_T3_geant2012" ] && [ -f "$OUT1/B2_K14_T3_geant2012/STATUS_COMPLETE" ] \
   && [ -s "$OUT1/B2_K14_T3_geant2012/provenance.tsv" ] \
   && [ -s "$OUT1/B2_K14_T3_geant2012/artifacts/bad/final_stats.csv" ] \
   && [ -s "$OUT1/B2_K14_T3_geant2012/artifacts/control/final_stats.csv" ] \
   && [ -s "$OUT1/B2_K14_T3_geant2012/console/benchmarks_final_b2_route_mapping_forced_distinct_K14_T3_geant2012_bad_depth4.log" ]; then
  pass "$ID" "principal selection creates full evidence for the selected configuration"
else
  fail_test "$ID" "principal selection creates full evidence for the selected configuration"
fi

ID=$(next_id "$ID")
OTHERS=0
for DIR in "$OUT1"/*/; do
  case "$(basename "$DIR")" in
    B2_K14_T3_geant2012) ;;
    *) OTHERS=$((OTHERS + 1)) ;;
  esac
done
if [ "$OTHERS" -eq 0 ]; then pass "$ID" "principal selection creates no evidence directories for unselected configurations"; else fail_test "$ID" "principal selection created $OTHERS unexpected evidence directories"; fi

ID=$(next_id "$ID")
if [ "$(docker_run_calls)" -eq 2 ]; then pass "$ID" "principal selection executes exactly one pair (2 docker runs)"; else fail_test "$ID" "principal selection executed $(docker_run_calls) docker runs instead of 2"; fi

# Invalid selection values must abort before anything runs.
for CASE in "EMPTY" "COMMA" "GLOB" "PATH" "SPACE" "UNKNOWN" "LOWERCASE"; do
  reset_mock_log
  OUTBAD="$TMP_ROOT/out-principal-bad-$CASE"
  mkdir -p "$OUTBAD"
  case "$CASE" in
    EMPTY)     VALUE="" ;;
    COMMA)     VALUE="B2_K14_T3_geant2012,B1_K8_T1_atlanta" ;;
    GLOB)      VALUE="B2_K14_*" ;;
    PATH)      VALUE="B2_K14_T3_geant2012/extra" ;;
    SPACE)     VALUE="B2_K14_T3_geant2012 extra" ;;
    UNKNOWN)   VALUE="B9_K14_T3_geant2012" ;;
    LOWERCASE) VALUE="b2_k14_t3_geant2012" ;;
  esac
  if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUTBAD" \
     RACELOOM_MATRIX_ONLY="$VALUE" \
     bash "$FAKE_REPO/scripts/run_final_matrix.sh" >"$TMP_ROOT/bad-$CASE.out" 2>&1; then
    RC=0
  else
    RC=$?
  fi
  ID=$(next_id "$ID")
  if [ "$RC" -eq 2 ] && [ "$(docker_run_calls)" -eq 0 ] && [ "$(status_rows "$OUTBAD")" -eq 0 ]; then
    pass "$ID" "principal selection rejects $CASE value before anything runs"
  else
    fail_test "$ID" "principal selection rejects $CASE value before anything runs (rc=$RC, runs=$(docker_run_calls), rows=$(status_rows "$OUTBAD"))"
  fi
done

# ---------------------------------------------------------------------------
# Principal launcher: selection then full run resumes
# ---------------------------------------------------------------------------

reset_mock_log
if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUT1" \
   bash "$FAKE_REPO/scripts/run_final_matrix.sh" >"$TMP_ROOT/t-resume.out" 2>&1; then
  RC=0
else
  RC=$?
fi
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ]; then pass "$ID" "full run after selection exits 0"; else fail_test "$ID" "full run after selection exits 0 (rc=$RC)"; fi

ID=$(next_id "$ID")
if [ "$(status_rows "$OUT1")" -eq 17 ]; then pass "$ID" "resume writes 16 new rows (1 skip + 15 run) on top of the selection row"; else fail_test "$ID" "resume status rows: $(status_rows "$OUT1") instead of 17"; fi

ID=$(next_id "$ID")
if [ "$(docker_run_calls)" -eq 30 ]; then pass "$ID" "resume executes only the remaining 15 configurations (30 docker runs)"; else fail_test "$ID" "resume executed $(docker_run_calls) docker runs instead of 30"; fi

ID=$(next_id "$ID")
if grep -q "SKIPPED_ALREADY_COMPLETE" "$OUT1/status.tsv" && [ "$(grep -c "SKIPPED_ALREADY_COMPLETE" "$OUT1/status.tsv")" -eq 1 ]; then
  pass "$ID" "resume skips the previously selected completed configuration"
else
  fail_test "$ID" "resume skips the previously selected completed configuration"
fi

# ---------------------------------------------------------------------------
# Supplementary launcher: selection mode
# ---------------------------------------------------------------------------

reset_mock_log
OUT2="$TMP_ROOT/out-supplementary-select"
mkdir -p "$OUT2"
if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUT2" \
   RACELOOM_MATRIX_ONLY=S2_hierarchical_extended_wrong_destination \
   bash "$FAKE_REPO/scripts/run_supplementary_matrix.sh" >"$TMP_ROOT/t-supp.out" 2>&1; then
  RC=0
else
  RC=$?
fi
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && [ "$(status_rows "$OUT2")" -eq 1 ] && [ "$(docker_run_calls)" -eq 2 ] \
   && [ -f "$OUT2/S2_hierarchical_extended_wrong_destination/STATUS_COMPLETE" ]; then
  pass "$ID" "supplementary selection runs exactly the selected configuration"
else
  fail_test "$ID" "supplementary selection runs exactly the selected configuration (rc=$RC, rows=$(status_rows "$OUT2"), runs=$(docker_run_calls))"
fi

reset_mock_log
OUT3="$TMP_ROOT/out-supplementary-bad"
mkdir -p "$OUT3"
if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUT3" \
   RACELOOM_MATRIX_ONLY=S1_multidomain,S3_multi_slice \
   bash "$FAKE_REPO/scripts/run_supplementary_matrix.sh" >"$TMP_ROOT/t-supp-bad.out" 2>&1; then
  RC=0
else
  RC=$?
fi
ID=$(next_id "$ID")
if [ "$RC" -eq 2 ] && [ "$(docker_run_calls)" -eq 0 ]; then
  pass "$ID" "supplementary selection rejects comma-separated values before anything runs"
else
  fail_test "$ID" "supplementary selection rejects comma-separated values (rc=$RC, runs=$(docker_run_calls))"
fi

# ---------------------------------------------------------------------------
# Non-git working tree (e.g. a release archive extracted from a zip):
# provenance must stay complete and the run must not be blocked. Runs last
# because it removes .git from the fake repository.
# ---------------------------------------------------------------------------

rm -rf "$FAKE_REPO/.git"
reset_mock_log
OUT4="$TMP_ROOT/out-nongit"
mkdir -p "$OUT4"
if RACELOOM_IMAGE=raceloom:latest RACELOOM_MATRIX_OUTPUT_ROOT="$OUT4" \
   RACELOOM_MATRIX_ONLY=S3_multi_slice_shared_core_isolation \
   bash "$FAKE_REPO/scripts/run_supplementary_matrix.sh" >"$TMP_ROOT/t-nongit.out" 2>&1; then
  RC=0
else
  RC=$?
fi
ID=$(next_id "$ID")
if [ "$RC" -eq 0 ] && [ -f "$OUT4/S3_multi_slice_shared_core_isolation/STATUS_COMPLETE" ] \
   && grep -q '^git_branch=not_a_git_repository$' "$OUT4/S3_multi_slice_shared_core_isolation/provenance.tsv" \
   && grep -q '^git_head=not_available$' "$OUT4/S3_multi_slice_shared_core_isolation/provenance.tsv" \
   && grep -Eq '^wt_fingerprint=[0-9a-f]{64}$' "$OUT4/S3_multi_slice_shared_core_isolation/provenance.tsv"; then
  pass "$ID" "non-git working tree completes with complete provenance"
else
  fail_test "$ID" "non-git working tree completes with complete provenance (rc=$RC)"; sed 's/^/    /' "$TMP_ROOT/t-nongit.out" | tail -5
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

printf '\n%s\n' "selection tests: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ] || exit 1
exit 0
