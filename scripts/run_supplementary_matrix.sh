#!/usr/bin/env bash
set -euo pipefail

STATUS_HEADER="$(printf 'config_id\tbenchmark\tdepth\tstatus\texit_code\tutc_start\tutc_end\tevidence_dir\tdetail')"
STATUS_TSV_NAME="status.tsv"
PROVENANCE_NAME="provenance.tsv"
LOCK_DIR_NAME=".supplementary_lock"
IN_PROGRESS_MARKER="STATUS_IN_PROGRESS"
COMPLETE_MARKER="STATUS_COMPLETE"

# Increment 43: supplementary S1-S4 synthetic benchmark group. Spec format is
# "bench|depth|config_id"; the config ID is explicit because the synthetic
# directory layout (benchmarks/synthetic/final/s< n >_<scenario>) does not
# follow the principal matrix family/topology layout. Depths and strategy are
# the documented execution parameters of docs/synthetic_s1_s4_matrix.tsv,
# docs/benchmark_runtimes_exact.tsv, the per-benchmark run_s<n>.sh defaults
# and the sanitized historical logs in docs/validation_logs/synthetic/.
MATRIX_SPECS=(
  "benchmarks/synthetic/final/s1_multidomain_wrong_destination|5|S1_multidomain_wrong_destination"
  "benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination|4|S2_hierarchical_extended_wrong_destination"
  "benchmarks/synthetic/final/s3_multi_slice_shared_core_isolation|5|S3_multi_slice_shared_core_isolation"
  "benchmarks/synthetic/final/s4_multi_region_stale_reroute|5|S4_multi_region_stale_reroute"
)

print_usage() {
  cat >&2 <<'EOF'
usage: RACELOOM_MATRIX_OUTPUT_ROOT=<existing-dir> bash scripts/run_supplementary_matrix.sh

Sequential, resumable launcher for the 4-configuration supplementary S1-S4
synthetic benchmark group (faulty side first), Increment 43.

Environment:
  RACELOOM_MATRIX_OUTPUT_ROOT
                      required: an EXISTING directory outside this repository
                      that receives the evidence. Relative paths resolve
                      against the invocation directory. Reuse the same root to
                      resume: completed configurations are skipped, incomplete
                      or failed ones are reported BLOCKED and never rerun
                      automatically. The root must not be "/" or any directory
                      inside this repository (symlinks are resolved).
  RACELOOM_IMAGE      required by the canonical pipeline: local RaceLoom
                      Docker image (e.g. raceloom:latest).
  RACELOOM_MATRIX_ONLY
                      optional: run exactly ONE existing configuration of the
                      supplementary group instead of all 4. The value must
                      equal one configuration ID exactly (e.g.
                      S1_multidomain_wrong_destination);
                      empty, unknown, comma-separated, glob-like or path-like
                      values abort before anything runs and never fall back
                      to the full group. Selection mode keeps every
                      preflight, provenance, status, marker, resume and
                      locking behavior; unselected configurations get no
                      evidence directories and no status records. Exit 0 in
                      selection mode means the SELECTED configuration
                      completed operationally only; it does NOT mean the full
                      4-configuration group was reproduced or scientifically
                      validated (the independent checker classifies the other
                      configurations as NOT_RUN). A later full-group
                      invocation with the same output root skips a completed
                      selected configuration and continues with the remaining
                      configurations in the original order.

Per configuration <ID> the launcher creates:
  <root>/<ID>/console/        console logs of both sides (pair-runner OUT_DIR)
  <root>/<ID>/artifacts/      RACELOOM_OUTPUT_DIR base; the canonical pair
                              runner creates bad/ and control/ itself
  <root>/<ID>/provenance.tsv  durable provenance record, written atomically
                              BEFORE the pair runner starts and never
                              overwritten afterwards; one key=value line per
                              field, covering benchmark identity, SHA-256
                              input integrity, runtime identity, repository
                              identity (branch, HEAD, working-tree
                              fingerprint), execution identity and relevant
                              environment identity
  <root>/<ID>/STATUS_IN_PROGRESS   durable in-progress marker
  <root>/<ID>/STATUS_COMPLETE      atomic success marker (exit 0 AND minimum
                              evidence: both console logs and both side-root
                              final_stats.csv files present and nonempty, AND
                              the provenance record preserved)

Root-level records:
  <root>/status.tsv           append-only, tab-separated, one record per
                              disposition; schema:
                              config_id benchmark depth status exit_code
                              utc_start utc_end evidence_dir detail
  <root>/.supplementary_lock/ concurrency lock; a stale lock must be
                              inspected and removed manually, never
                              automatically.

Statuses: COMPLETE (operationally completed with preserved minimum evidence;
NOT scientific validation against historical expectations), FAILED, BLOCKED,
SKIPPED_ALREADY_COMPLETE.

Exit codes: 0 all scheduled configurations COMPLETE or
SKIPPED_ALREADY_COMPLETE (in selection mode this refers to the single
selected configuration only); 1 at least one scheduled configuration FAILED
or BLOCKED; 2 environment or usage error.
EOF
}

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 2
}

now_utc() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

config_id_for() {
  # Parse one MATRIX_SPECS entry "bench|depth|config_id" into the globals
  # BENCH, DEPTH and CFG_ID. Aborts on malformed specs before anything runs.
  local spec="$1"
  local bench depth cfg_id
  IFS='|' read -r bench depth cfg_id <<< "$spec" || die "cannot parse specification: $spec"
  case "$cfg_id" in
    *'|'*) die "specification must have exactly three |-separated fields: $spec" ;;
  esac
  [ -n "$bench" ] && [ -n "$depth" ] && [ -n "$cfg_id" ] \
    || die "specification has an empty field: $spec"
  case "$cfg_id" in
    *'/'*|*' '*|*$'\t'*|*$'\n'*) die "invalid configuration ID in specification: $spec" ;;
  esac
  case "$depth" in
    ''|*[!0-9]*) die "invalid depth in specification: $spec (must be a non-negative integer)" ;;
  esac
  BENCH="$bench"
  DEPTH="$depth"
  CFG_ID="$cfg_id"
}

append_record() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" >> "$STATUS_TSV"
}

atomic_write_lines() {
  local dest="$1"
  shift
  local tmp="${dest}.tmp.$$"
  printf '%s\n' "$@" > "$tmp" || { rm -f "$tmp" 2>/dev/null || true; return 1; }
  mv -f "$tmp" "$dest" || { rm -f "$tmp" 2>/dev/null || true; return 1; }
}

# ---------------------------------------------------------------------------
# Provenance support (Increment 37). All hashing uses a portable SHA-256
# utility detected at startup; no third-party dependencies are introduced.
# ---------------------------------------------------------------------------

detect_sha256() {
  if command -v shasum >/dev/null 2>&1 && shasum -a 256 /dev/null >/dev/null 2>&1; then
    SHA256_KIND="shasum"
    SHA256_TOOL="shasum -a 256"
  elif command -v sha256sum >/dev/null 2>&1 && sha256sum /dev/null >/dev/null 2>&1; then
    SHA256_KIND="sha256sum"
    SHA256_TOOL="sha256sum"
  else
    die "no SHA-256 utility available (tried 'shasum -a 256' and 'sha256sum'); provenance records require SHA-256 hashing"
  fi
}

# Print "<hash>  <path>" for one file; nonzero on any failure.
sha256_line() {
  case "$SHA256_KIND" in
    shasum) shasum -a 256 -- "$1" ;;
    sha256sum) sha256sum -- "$1" ;;
    *) return 1 ;;
  esac
}

# Print only the hexadecimal SHA-256 of one file; nonzero on any failure.
sha256_of() {
  local out
  out="$(sha256_line "$1")" || return 1
  printf '%s\n' "$out" | awk '{print $1}'
}

# Compute the working-tree fingerprint in an isolated subshell.
# Prints three lines on stdout: fingerprint, tracked-file count,
# untracked-non-ignored-file count. Exit code 3 signals a repository path
# containing a newline character. Never modifies Git state.
# Algorithm: manifest of '<sha256>  <repo-relative-path>' lines over every
# git-tracked file (git ls-files --cached) plus every untracked non-ignored
# file (git ls-files --others --exclude-standard), LC_ALL=C-sorted by path;
# contents batch-hashed with the detected SHA-256 utility; entries that
# cannot be hashed are recorded as 'MISSING<TAB>path' lines before the
# hashed lines; .git internals and git-ignored files are excluded.
compute_wt_fingerprint() (
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/raceloom-wtfp.XXXXXX")" || exit 1
  trap 'rm -rf "$tmp_dir"' EXIT
  nul="$tmp_dir/paths.nul"
  git -C "$REPO_ROOT" ls-files -z --cached > "$nul" || exit 1
  git -C "$REPO_ROOT" ls-files -z --others --exclude-standard >> "$nul" || exit 1
  entry_n="$(tr -cd '\000' < "$nul" | wc -c | tr -d '[:space:]')" || exit 1
  tr '\000' '\012' < "$nul" | LC_ALL=C sort -u > "$tmp_dir/paths.sorted" || exit 1
  line_n="$(wc -l < "$tmp_dir/paths.sorted" | tr -d '[:space:]')" || exit 1
  [ "$entry_n" = "$line_n" ] || exit 3
  : > "$tmp_dir/req.nul"
  : > "$tmp_dir/manifest"
  while IFS= read -r p; do
    if [ -f "$p" ] || [ -L "$p" ]; then
      printf '%s\0' "$p" >> "$tmp_dir/req.nul"
    else
      printf 'MISSING\t%s\n' "$p" >> "$tmp_dir/manifest"
    fi
  done < "$tmp_dir/paths.sorted"
  if [ -s "$tmp_dir/req.nul" ]; then
    case "$SHA256_KIND" in
      shasum) xargs -0 shasum -a 256 -- < "$tmp_dir/req.nul" >> "$tmp_dir/manifest" || exit 1 ;;
      sha256sum) xargs -0 sha256sum -- < "$tmp_dir/req.nul" >> "$tmp_dir/manifest" || exit 1 ;;
      *) exit 1 ;;
    esac
  fi
  tracked_n="$(git -C "$REPO_ROOT" ls-files --cached | wc -l | tr -d '[:space:]')" || exit 1
  untracked_n="$(git -C "$REPO_ROOT" ls-files --others --exclude-standard | wc -l | tr -d '[:space:]')" || exit 1
  fingerprint="$(sha256_of "$tmp_dir/manifest")" || exit 1
  printf '%s\n%s\n%s\n' "$fingerprint" "$tracked_n" "$untracked_n"
)

# Fingerprint fallback for working trees without git (e.g. release archives
# extracted from a zip). Prints one line: the fingerprint. Manifest: every
# regular file under the repository root except .git/ internals and the
# generated directories and patterns recorded in .gitignore, LC_ALL=C-sorted
# by repo-relative path. Never modifies anything.
compute_wt_fingerprint_nongit() (
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/raceloom-wtfp-ng.XXXXXX")" || exit 1
  trap 'rm -rf "$tmp_dir"' EXIT
  : > "$tmp_dir/manifest"
  cd "$REPO_ROOT" || exit 1
  find . \
    -name .git -prune -o \
    -name results -prune -o \
    -name output -prune -o \
    -name progress_logs -prune -o \
    -name __pycache__ -prune -o \
    -name reproduced_paper_numbers -prune -o \
    -type f -print | sed 's|^\./||' | LC_ALL=C sort > "$tmp_dir/paths.sorted" || exit 1
  while IFS= read -r p; do
    case "$p" in
      *.pyc|*.log|*.nohup.log|*.tar.gz|.DS_Store) continue ;;
    esac
    [ -f "$p" ] || continue
    sha256_line "$p" >> "$tmp_dir/manifest" || exit 1
  done < "$tmp_dir/paths.sorted"
  sha256_of "$tmp_dir/manifest"
)

# Write the per-configuration provenance record atomically BEFORE the pair
# runner starts. On any failure sets PROVENANCE_ERROR and returns nonzero;
# the caller must not start the benchmark in that case.
write_provenance() {
  PROVENANCE_ERROR=""
  local cfg_id="$1" bench="$2" depth="$3" cfg_dir="$4" console_dir="$5" artifacts_dir="$6"
  local dest="$cfg_dir/$PROVENANCE_NAME"

  if [ -e "$dest" ] || [ -L "$dest" ]; then
    PROVENANCE_ERROR="existing provenance record found before a new attempt; not overwritten: $dest"
    return 1
  fi

  local bad_model="$REPO_ROOT/$bench/bad/model.json"
  local bad_props="$REPO_ROOT/$bench/bad/properties.json"
  local control_model="$REPO_ROOT/$bench/control/model.json"
  local control_props="$REPO_ROOT/$bench/control/properties.json"

  local h_bad_model h_bad_props h_control_model h_control_props
  h_bad_model="$(sha256_of "$bad_model")" \
    || { PROVENANCE_ERROR="cannot hash bad model input: $bad_model"; return 1; }
  h_bad_props="$(sha256_of "$bad_props")" \
    || { PROVENANCE_ERROR="cannot hash bad properties input: $bad_props"; return 1; }
  h_control_model="$(sha256_of "$control_model")" \
    || { PROVENANCE_ERROR="cannot hash control model input: $control_model"; return 1; }
  h_control_props="$(sha256_of "$control_props")" \
    || { PROVENANCE_ERROR="cannot hash control properties input: $control_props"; return 1; }

  local resolved_image_id image_arch image_repo_digest
  resolved_image_id="$(docker image inspect --format '{{.Id}}' "$RACELOOM_IMAGE" 2>/dev/null)" \
    || { PROVENANCE_ERROR="cannot resolve docker image id for RACELOOM_IMAGE='$RACELOOM_IMAGE'"; return 1; }
  image_arch="$(docker image inspect --format '{{.Architecture}}' "$RACELOOM_IMAGE" 2>/dev/null)" || image_arch=""
  [ -n "$image_arch" ] || image_arch="unknown"
  image_repo_digest="$(docker image inspect --format '{{.RepoDigests}}' "$RACELOOM_IMAGE" 2>/dev/null)" || image_repo_digest=""
  case "$image_repo_digest" in
    ""|"[]") image_repo_digest="not_available" ;;
  esac

  local h_pair h_wrapper h_launcher
  h_pair="$(sha256_of "$PAIR_RUNNER")" \
    || { PROVENANCE_ERROR="cannot hash pair runner: $PAIR_RUNNER"; return 1; }
  h_wrapper="$(sha256_of "$DOCKER_WRAPPER")" \
    || { PROVENANCE_ERROR="cannot hash docker wrapper: $DOCKER_WRAPPER"; return 1; }
  h_launcher="$(sha256_of "$LAUNCHER_SCRIPT")" \
    || { PROVENANCE_ERROR="cannot hash executing launcher: $LAUNCHER_SCRIPT"; return 1; }

  local git_branch git_head wt_state wt_fingerprint fp_algorithm_note
  local wt_tracked wt_untracked
  if command -v git >/dev/null 2>&1 && git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git_branch="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)" \
      || { PROVENANCE_ERROR="cannot determine repository branch"; return 1; }
    git_head="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null)" \
      || { PROVENANCE_ERROR="cannot determine repository HEAD"; return 1; }
    local git_status_out
    git_status_out="$(LC_ALL=C GIT_OPTIONAL_LOCKS=0 git -C "$REPO_ROOT" status --porcelain=v1 2>/dev/null)" \
      || { PROVENANCE_ERROR="cannot determine git working-tree state"; return 1; }
    if [ -z "$git_status_out" ]; then
      wt_state="clean"
    else
      wt_state="dirty"
    fi

    local fp_out fp_rc
    fp_rc=0
    fp_out="$(compute_wt_fingerprint)" || fp_rc=$?
    if [ "$fp_rc" -ne 0 ]; then
      if [ "$fp_rc" -eq 3 ]; then
        PROVENANCE_ERROR="working-tree fingerprint failed: repository file paths contain newline characters"
      else
        PROVENANCE_ERROR="working-tree fingerprint computation failed (git unavailable or unexpected repository state)"
      fi
      return 1
    fi
    wt_fingerprint="$(printf '%s\n' "$fp_out" | sed -n '1p')"
    wt_tracked="$(printf '%s\n' "$fp_out" | sed -n '2p')"
    wt_untracked="$(printf '%s\n' "$fp_out" | sed -n '3p')"
    fp_algorithm_note="sha256 of a manifest listing every git-tracked file (git ls-files --cached) plus every untracked non-ignored file (git ls-files --others --exclude-standard) as '<hash>  <repo-relative-path>' lines in LC_ALL=C path order; contents hashed with $SHA256_TOOL; unhashable entries emit MISSING lines; .git internals and git-ignored files are excluded"
  else
    # Release archives are frequently extracted without a .git directory
    # (e.g. a Zenodo zip). Provenance stays complete: the repository
    # identity is recorded as unavailable and the extracted tree itself is
    # fingerprinted. The independent checker treats these values as
    # informational and never classifies on them.
    git_branch="not_a_git_repository"
    git_head="not_available"
    wt_state="not_a_git_repository"
    local fp_rc_ng
    fp_rc_ng=0
    wt_fingerprint="$(compute_wt_fingerprint_nongit)" || fp_rc_ng=$?
    if [ "$fp_rc_ng" -ne 0 ] || [ -z "$wt_fingerprint" ]; then
      PROVENANCE_ERROR="working-tree fingerprint computation failed (non-git working tree)"
      return 1
    fi
    wt_tracked="not_available"
    wt_untracked="not_available"
    fp_algorithm_note="sha256 of a manifest listing every regular file under the repository root except .git/ internals and the generated directories and patterns recorded in .gitignore (results/, output/, progress_logs/, __pycache__/, reproduced_paper_numbers/, *.pyc, *.log, *.tar.gz, .DS_Store) as '<hash>  <repo-relative-path>' lines in LC_ALL=C path order; computed without git because the working tree is not a git checkout"
  fi

  local docker_client_ver docker_server_ver
  docker_client_ver="$(docker version --format '{{.Client.Version}}' 2>/dev/null)" || docker_client_ver=""
  [ -n "$docker_client_ver" ] || docker_client_ver="unknown"
  docker_server_ver="$(docker version --format '{{.Server.Version}}' 2>/dev/null)" || docker_server_ver=""
  [ -n "$docker_server_ver" ] || docker_server_ver="unknown"

  local host_name host_arch host_python
  host_name="$(uname -n 2>/dev/null)" || host_name="unknown"
  [ -n "$host_name" ] || host_name="unknown"
  host_arch="$(uname -m 2>/dev/null)" || host_arch="unknown"
  [ -n "$host_arch" ] || host_arch="unknown"
  if command -v python3 >/dev/null 2>&1; then
    host_python="$(python3 -c 'import sys; sys.stdout.write("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)" || host_python=""
    [ -n "$host_python" ] || host_python="unknown"
  else
    host_python="not_available"
  fi

  local prepared_ts
  prepared_ts="$(now_utc)"

  atomic_write_lines "$dest" \
    "provenance_schema=raceloom-matrix-provenance-v1" \
    "config_id=$cfg_id" \
    "benchmark=$bench" \
    "depth=$depth" \
    "strategy=bfs" \
    "execution_order=bad_then_control" \
    "bad_model_path=$bad_model" \
    "bad_properties_path=$bad_props" \
    "control_model_path=$control_model" \
    "control_properties_path=$control_props" \
    "sha256_bad_model=$h_bad_model" \
    "sha256_bad_properties=$h_bad_props" \
    "sha256_control_model=$h_control_model" \
    "sha256_control_properties=$h_control_props" \
    "sha256_tool=$SHA256_TOOL" \
    "requested_image=$RACELOOM_IMAGE" \
    "resolved_image_id=$resolved_image_id" \
    "image_architecture=$image_arch" \
    "image_repo_digest=$image_repo_digest" \
    "sha256_run_one_pair_sh=$h_pair" \
    "sha256_run_raceloom_progress_sh=$h_wrapper" \
    "sha256_run_final_matrix_sh=$h_launcher" \
    "note_sha256_run_final_matrix_sh=hash of the executing supplementary launcher script itself (scripts/run_supplementary_matrix.sh at execution time; schema key name retained from the principal provenance schema v1); image id is the local docker image id, not a registry manifest digest" \
    "git_branch=$git_branch" \
    "git_head=$git_head" \
    "git_worktree_state=$wt_state" \
    "wt_fingerprint=$wt_fingerprint" \
    "wt_fingerprint_algorithm=$fp_algorithm_note" \
    "wt_fingerprint_utc=$prepared_ts" \
    "wt_tracked_files=$wt_tracked" \
    "wt_untracked_nonignored_files=$wt_untracked" \
    "pair_runner_command=RACELOOM_OUTPUT_DIR=$artifacts_dir scripts/run_one_pair.sh $bench $depth $console_dir" \
    "pair_runner_arg_bench=$bench" \
    "pair_runner_arg_depth=$depth" \
    "pair_runner_arg_out_dir=$console_dir" \
    "pair_runner_env_RACELOOM_OUTPUT_DIR=$artifacts_dir" \
    "console_dir=$console_dir" \
    "artifacts_base_dir=$artifacts_dir" \
    "utc_prepared=$prepared_ts" \
    "utc_prepared_note=provenance creation time in UTC before pair execution; execution start/end and exit status are owned by status.tsv and the marker files" \
    "host_hostname=$host_name" \
    "host_architecture=$host_arch" \
    "docker_client_version=$docker_client_ver" \
    "docker_server_version=$docker_server_ver" \
    "host_python3_version=$host_python" \
    "runtime_python_version=not_recorded" \
    "runtime_python_version_note=determining the container runtime python version would require starting a docker container outside benchmark execution; intentionally not queried" \
    || { PROVENANCE_ERROR="cannot write provenance record: $dest"; return 1; }

  [ -s "$dest" ] || { PROVENANCE_ERROR="provenance record is empty after write: $dest"; return 1; }
  return 0
}

evidence_ok() {
  local cfg_dir="$1"
  local log_base="$2"
  local depth="$3"
  [ -d "$cfg_dir/artifacts/bad" ] || return 1
  [ -d "$cfg_dir/artifacts/control" ] || return 1
  [ -s "$cfg_dir/console/${log_base}_bad_depth${depth}.log" ] || return 1
  [ -s "$cfg_dir/console/${log_base}_control_depth${depth}.log" ] || return 1
  [ -s "$cfg_dir/artifacts/bad/final_stats.csv" ] || return 1
  [ -s "$cfg_dir/artifacts/control/final_stats.csv" ] || return 1
  return 0
}

marker_field() {
  local marker="$1"
  local key="$2"
  sed -n "/^${key}=/{s/^${key}=//p;q;}" "$marker" 2>/dev/null
}

valid_complete_marker() {
  local cfg_dir="$1"
  local cfg_id="$2"
  local depth="$3"
  local marker="$cfg_dir/$COMPLETE_MARKER"
  local mid mdepth
  RESUME_MARKER_EXIT_CODE="-"
  [ -f "$marker" ] || return 1
  [ ! -L "$marker" ] || return 1
  [ ! -e "$cfg_dir/$IN_PROGRESS_MARKER" ] || return 1
  mid="$(marker_field "$marker" config_id)" || return 1
  [ "$mid" = "$cfg_id" ] || return 1
  mdepth="$(marker_field "$marker" depth)" || return 1
  [ "$mdepth" = "$depth" ] || return 1
  RESUME_MARKER_EXIT_CODE="$(marker_field "$marker" exit_code)" || RESUME_MARKER_EXIT_CODE="-"
  [ -n "$RESUME_MARKER_EXIT_CODE" ] || RESUME_MARKER_EXIT_CODE="-"
  return 0
}

evaluate_existing() {
  local cfg_dir="$1"
  local cfg_id="$2"
  local log_base="$3"
  local depth="$4"
  RESUME_DETAIL="existing incomplete, failed, or unrecognized evidence; not rerun automatically; manual recovery required"
  RESUME_EXIT_CODE="-"
  if valid_complete_marker "$cfg_dir" "$cfg_id" "$depth" && evidence_ok "$cfg_dir" "$log_base" "$depth"; then
    RESUME_EXIT_CODE="$RESUME_MARKER_EXIT_CODE"
    return 0
  fi
  if [ -f "$cfg_dir/$COMPLETE_MARKER" ]; then
    RESUME_DETAIL="completion marker present but minimum evidence missing, empty, or inconsistent; manual recovery required"
  elif [ -f "$cfg_dir/$IN_PROGRESS_MARKER" ]; then
    RESUME_DETAIL="interrupted or in-progress evidence found; not rerun automatically; manual recovery required"
  fi
  return 1
}

cleanup_lock() {
  if [ "${LOCK_ACQUIRED:-0}" = "1" ] && [ -n "${LOCK_DIR:-}" ] && [ -d "$LOCK_DIR" ]; then
    local owner_pid
    owner_pid="$(cat "$LOCK_DIR/owner.pid" 2>/dev/null || true)"
    if [ "$owner_pid" = "$$" ] || [ -z "$(ls -A "$LOCK_DIR" 2>/dev/null)" ]; then
      rm -f "$LOCK_DIR/owner.pid" 2>/dev/null || true
      rmdir "$LOCK_DIR" 2>/dev/null || true
    fi
  fi
  return 0
}
trap cleanup_lock EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if [ "$#" -gt 0 ]; then
  case "$1" in
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      printf 'ERROR: unexpected argument: %s\n\n' "$1" >&2
      print_usage
      exit 2
      ;;
  esac
fi

if [ "${RACELOOM_MATRIX_OUTPUT_ROOT+x}" != x ]; then
  printf 'ERROR: RACELOOM_MATRIX_OUTPUT_ROOT is not set; export it to an existing directory outside this repository before launching the matrix\n\n' >&2
  print_usage
  exit 2
fi
if [ -z "$RACELOOM_MATRIX_OUTPUT_ROOT" ]; then
  printf 'ERROR: RACELOOM_MATRIX_OUTPUT_ROOT is set but empty; export it to an existing directory outside this repository\n\n' >&2
  print_usage
  exit 2
fi
case "$RACELOOM_MATRIX_OUTPUT_ROOT" in
  -*)
    die "RACELOOM_MATRIX_OUTPUT_ROOT must be a directory path, not an option-like value: $RACELOOM_MATRIX_OUTPUT_ROOT"
    ;;
esac
MATRIX_ROOT="$(cd "$RACELOOM_MATRIX_OUTPUT_ROOT" 2>/dev/null && pwd -P)" \
  || die "RACELOOM_MATRIX_OUTPUT_ROOT='$RACELOOM_MATRIX_OUTPUT_ROOT' is not an existing, accessible directory (relative paths resolve against the invocation directory)"
if [ "$MATRIX_ROOT" = "/" ]; then
  die "RACELOOM_MATRIX_OUTPUT_ROOT resolves to the filesystem root; choose a dedicated directory outside the repository"
fi
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
LAUNCHER_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
cd "$REPO_ROOT" || die "cannot change directory to the benchmark repository root: $REPO_ROOT"
case "$MATRIX_ROOT" in
  "$REPO_ROOT"|"$REPO_ROOT"/*)
    die "RACELOOM_MATRIX_OUTPUT_ROOT resolves to '$MATRIX_ROOT', inside the benchmark repository ($REPO_ROOT); choose a host directory outside the repository"
    ;;
esac
case "$MATRIX_ROOT" in
  *$'\t'*|*$'\n'*)
    die "RACELOOM_MATRIX_OUTPUT_ROOT must not contain tab or newline characters (provenance records are tab-separated): $MATRIX_ROOT"
    ;;
esac
if [ ! -r "$MATRIX_ROOT" ] || [ ! -w "$MATRIX_ROOT" ] || [ ! -x "$MATRIX_ROOT" ]; then
  die "matrix output root is not readable/writable/executable: $MATRIX_ROOT"
fi

# ---------------------------------------------------------------------------
# Increment 39: optional single-configuration selection.
# RACELOOM_MATRIX_ONLY, when set, must equal exactly one existing matrix
# configuration ID derived from MATRIX_SPECS; the launcher then schedules only
# that configuration with all normal preflight, provenance, status, marker,
# resume and locking behavior. Any other value (empty, unknown, comma-
# separated, glob-like, path-like) is a usage error that aborts before
# anything runs; it never falls back to the full matrix. When the variable is
# unset, all 4 configurations are scheduled exactly as before.
# ---------------------------------------------------------------------------
MATRIX_ONLY_SET=0
if [ "${RACELOOM_MATRIX_ONLY+x}" = x ]; then
  MATRIX_ONLY_SET=1
  if [ -z "$RACELOOM_MATRIX_ONLY" ]; then
    die "RACELOOM_MATRIX_ONLY is set but empty; unset it to run the full 4-configuration supplementary group, or set it to exactly one existing configuration ID (e.g. S1_multidomain_wrong_destination)"
  fi
  case "$RACELOOM_MATRIX_ONLY" in
    *$'\t'*|*$'\n'*)
      die "RACELOOM_MATRIX_ONLY must not contain tab or newline characters: '$RACELOOM_MATRIX_ONLY'"
      ;;
  esac
  case "$RACELOOM_MATRIX_ONLY" in
    *,*)
      die "RACELOOM_MATRIX_ONLY must be exactly one configuration ID; comma-separated lists are not supported: '$RACELOOM_MATRIX_ONLY'"
      ;;
  esac
  case "$RACELOOM_MATRIX_ONLY" in
    */*|*\**|*\?*|*\[*|*' '*)
      die "RACELOOM_MATRIX_ONLY must be a bare configuration ID, not a path or glob pattern: '$RACELOOM_MATRIX_ONLY'"
      ;;
  esac
  MATRIX_ONLY_VALID_IDS=""
  for SPEC in "${MATRIX_SPECS[@]}"; do
    config_id_for "$SPEC"
    MATRIX_ONLY_CANDIDATE="$CFG_ID"
    if [ -z "$MATRIX_ONLY_VALID_IDS" ]; then
      MATRIX_ONLY_VALID_IDS="$MATRIX_ONLY_CANDIDATE"
    else
      MATRIX_ONLY_VALID_IDS="$MATRIX_ONLY_VALID_IDS
$MATRIX_ONLY_CANDIDATE"
    fi
  done
  if ! printf '%s\n' "$MATRIX_ONLY_VALID_IDS" | grep -Fxq -- "$RACELOOM_MATRIX_ONLY"; then
    die "RACELOOM_MATRIX_ONLY='$RACELOOM_MATRIX_ONLY' does not exactly match any existing matrix configuration ID; valid IDs are:
$MATRIX_ONLY_VALID_IDS"
  fi
  printf '[supplementary] selection mode: RACELOOM_MATRIX_ONLY=%s; only this configuration will be scheduled (1 of 4)\n' "$RACELOOM_MATRIX_ONLY"
fi

PAIR_RUNNER="$REPO_ROOT/scripts/run_one_pair.sh"
DOCKER_WRAPPER="$REPO_ROOT/scripts/run_raceloom_progress.sh"
[ -f "$PAIR_RUNNER" ] || die "canonical pair runner not found: scripts/run_one_pair.sh (expected under $REPO_ROOT)"
[ -x "$PAIR_RUNNER" ] || die "canonical pair runner is not executable: $PAIR_RUNNER"
[ -f "$DOCKER_WRAPPER" ] || die "canonical docker wrapper not found: scripts/run_raceloom_progress.sh (expected under $REPO_ROOT)"
[ -d "$REPO_ROOT/benchmarks/synthetic/final" ] || die "benchmark root not found: $REPO_ROOT/benchmarks/synthetic/final"

LOCK_DIR="$MATRIX_ROOT/$LOCK_DIR_NAME"
LOCK_ACQUIRED=0
if mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_ACQUIRED=1
  printf '%s\n' "$$" > "$LOCK_DIR/owner.pid" 2>/dev/null || true
else
  if [ -d "$LOCK_DIR" ]; then
    LOCK_OWNER="$(cat "$LOCK_DIR/owner.pid" 2>/dev/null || true)"
    [ -n "$LOCK_OWNER" ] || LOCK_OWNER="unknown"
    die "matrix lock already exists: $LOCK_DIR (owner pid: $LOCK_OWNER); another matrix process may be running with this output root; if no matrix process is running, inspect and remove the stale lock manually"
  fi
  die "cannot create matrix lock directory: $LOCK_DIR"
fi

command -v docker >/dev/null 2>&1 || die "docker executable not found in PATH; install/start Docker and retry"
docker info >/dev/null 2>&1 || die "docker daemon not accessible; start Docker and retry"
if [ -z "${RACELOOM_IMAGE:-}" ]; then
  die "RACELOOM_IMAGE is not set; RaceLoom is distributed separately (Zenodo record 16884345, see scripts/setup_raceloom_artifact.sh); export RACELOOM_IMAGE=<image>:<tag>"
fi
case "$RACELOOM_IMAGE" in
  *$'\t'*|*$'\n'*)
    die "RACELOOM_IMAGE must not contain tab or newline characters (provenance records are tab-separated)"
    ;;
esac
docker image inspect "$RACELOOM_IMAGE" >/dev/null 2>&1 \
  || die "RACELOOM_IMAGE='$RACELOOM_IMAGE' not found in local Docker images; load or build the RaceLoom image first (see scripts/setup_raceloom_artifact.sh)"
detect_sha256

STATUS_TSV="$MATRIX_ROOT/$STATUS_TSV_NAME"
if [ -L "$STATUS_TSV" ]; then
  die "status file must be a regular file, not a symlink: $STATUS_TSV"
fi
if [ -e "$STATUS_TSV" ]; then
  if [ ! -f "$STATUS_TSV" ]; then
    die "status file exists but is not a regular file: $STATUS_TSV"
  fi
  if [ ! -s "$STATUS_TSV" ]; then
    atomic_write_lines "$STATUS_TSV" "$STATUS_HEADER"
  fi
  STATUS_FIRST_LINE="$(head -n 1 "$STATUS_TSV")"
  if [ "$STATUS_FIRST_LINE" != "$STATUS_HEADER" ]; then
    die "existing $STATUS_TSV does not match the expected matrix status schema; refusing to append; inspect the file and choose a fresh output root if it belongs to something else"
  fi
else
  atomic_write_lines "$STATUS_TSV" "$STATUS_HEADER"
fi

SEEN_IDS=""
for SPEC in "${MATRIX_SPECS[@]}"; do
  config_id_for "$SPEC"
  for SIDE in bad control; do
    for INPUT in model.json properties.json; do
      [ -f "$REPO_ROOT/$BENCH/$SIDE/$INPUT" ] || die "missing benchmark input: $BENCH/$SIDE/$INPUT"
    done
  done
  if [ -n "$SEEN_IDS" ] && grep -Fxq -- "$CFG_ID" <<< "$SEEN_IDS"; then
    die "duplicate configuration identifier derived for $BENCH: $CFG_ID"
  fi
  if [ -n "$SEEN_IDS" ]; then
    SEEN_IDS="$SEEN_IDS
$CFG_ID"
  else
    SEEN_IDS="$CFG_ID"
  fi
  CFG_DIR="$MATRIX_ROOT/$CFG_ID"
  if [ -L "$CFG_DIR" ] || { [ -e "$CFG_DIR" ] && [ ! -d "$CFG_DIR" ]; }; then
    die "output-path collision for configuration $CFG_ID: $CFG_DIR exists and is not a usable directory; resolve the collision manually or choose a different output root"
  fi
done

N_COMPLETE=0
N_SKIPPED=0
N_FAILED=0
N_BLOCKED=0
OVERALL=0

# Increment 39: schedule the full matrix by default, or exactly the one
# configuration matching a validated RACELOOM_MATRIX_ONLY value. The filter
# selects from the existing MATRIX_SPECS list; no separate specification list
# is maintained.
RUN_SPECS=("${MATRIX_SPECS[@]}")
if [ "$MATRIX_ONLY_SET" = 1 ]; then
  RUN_SPECS=()
  for SPEC in "${MATRIX_SPECS[@]}"; do
    config_id_for "$SPEC"
    if [ "$CFG_ID" = "$RACELOOM_MATRIX_ONLY" ]; then
      RUN_SPECS+=("$SPEC")
    fi
  done
fi

for SPEC in "${RUN_SPECS[@]}"; do
  config_id_for "$SPEC"
  LOG_BASE="$(printf '%s' "$BENCH" | tr '/' '_')"
  CFG_DIR="$MATRIX_ROOT/$CFG_ID"
  CONSOLE_DIR="$CFG_DIR/console"
  ARTIFACTS_DIR="$CFG_DIR/artifacts"

  if [ -d "$CFG_DIR" ]; then
    RESUME_MARKER_EXIT_CODE="-"
    if evaluate_existing "$CFG_DIR" "$CFG_ID" "$LOG_BASE" "$DEPTH"; then
      NOW="$(now_utc)"
      append_record "$CFG_ID" "$BENCH" "$DEPTH" "SKIPPED_ALREADY_COMPLETE" "$RESUME_MARKER_EXIT_CODE" "$NOW" "$NOW" "$CFG_DIR" "valid completion evidence found; skipped without executing"
      printf '[supplementary] SKIP      %s (valid completion evidence)\n' "$CFG_ID"
      N_SKIPPED=$((N_SKIPPED + 1))
    else
      NOW="$(now_utc)"
      append_record "$CFG_ID" "$BENCH" "$DEPTH" "BLOCKED" "-" "$NOW" "$NOW" "$CFG_DIR" "$RESUME_DETAIL"
      printf '[supplementary] BLOCKED   %s (%s)\n' "$CFG_ID" "$RESUME_DETAIL"
      N_BLOCKED=$((N_BLOCKED + 1))
      OVERALL=1
    fi
    continue
  fi

  printf '[supplementary] RUN       %s bench=%s depth=%s\n' "$CFG_ID" "$BENCH" "$DEPTH"
  mkdir "$CFG_DIR" || die "cannot create configuration directory: $CFG_DIR"
  mkdir "$CONSOLE_DIR" || die "cannot create console directory: $CONSOLE_DIR"
  mkdir "$ARTIFACTS_DIR" || die "cannot create artifacts directory: $ARTIFACTS_DIR"
  if [ -e "$ARTIFACTS_DIR/bad" ] || [ -L "$ARTIFACTS_DIR/bad" ] || [ -e "$ARTIFACTS_DIR/control" ] || [ -L "$ARTIFACTS_DIR/control" ]; then
    die "side artifact directory already exists before pair invocation: $ARTIFACTS_DIR; the canonical pair runner owns bad/ and control/"
  fi

  START_TS="$(now_utc)"
  if ! write_provenance "$CFG_ID" "$BENCH" "$DEPTH" "$CFG_DIR" "$CONSOLE_DIR" "$ARTIFACTS_DIR"; then
    NOW="$(now_utc)"
    append_record "$CFG_ID" "$BENCH" "$DEPTH" "BLOCKED" "-" "$NOW" "$NOW" "$CFG_DIR" \
      "$PROVENANCE_ERROR; benchmark not started"
    printf '[supplementary] BLOCKED   %s (%s)\n' "$CFG_ID" "$PROVENANCE_ERROR"
    N_BLOCKED=$((N_BLOCKED + 1))
    OVERALL=1
    continue
  fi
  atomic_write_lines "$CFG_DIR/$IN_PROGRESS_MARKER" \
    "config_id=$CFG_ID" \
    "benchmark=$BENCH" \
    "depth=$DEPTH" \
    "utc_start=$START_TS" \
    "pid=$$"

  RC=0
  RACELOOM_OUTPUT_DIR="$ARTIFACTS_DIR" scripts/run_one_pair.sh "$BENCH" "$DEPTH" "$CONSOLE_DIR" || RC=$?
  END_TS="$(now_utc)"

  rm -f "$CFG_DIR/$IN_PROGRESS_MARKER" 2>/dev/null || true

  if [ "$RC" -eq 0 ] && evidence_ok "$CFG_DIR" "$LOG_BASE" "$DEPTH" && [ -s "$CFG_DIR/$PROVENANCE_NAME" ]; then
    atomic_write_lines "$CFG_DIR/$COMPLETE_MARKER" \
      "config_id=$CFG_ID" \
      "benchmark=$BENCH" \
      "depth=$DEPTH" \
      "exit_code=0" \
      "utc_start=$START_TS" \
      "utc_end=$END_TS" \
      "evidence_dir=$CFG_DIR"
    append_record "$CFG_ID" "$BENCH" "$DEPTH" "COMPLETE" "0" "$START_TS" "$END_TS" "$CFG_DIR" "pair runner exited 0 with preserved minimum evidence and provenance; not scientifically validated"
    printf '[supplementary] COMPLETE  %s\n' "$CFG_ID"
    N_COMPLETE=$((N_COMPLETE + 1))
  else
    if [ "$RC" -eq 0 ] && [ ! -s "$CFG_DIR/$PROVENANCE_NAME" ]; then
      DETAIL="pair runner exited 0 but the provenance record is missing or empty; operational completion refused"
    elif [ "$RC" -eq 0 ]; then
      DETAIL="pair runner exited 0 but minimum evidence is missing or empty"
    else
      DETAIL="pair runner failed"
    fi
    append_record "$CFG_ID" "$BENCH" "$DEPTH" "FAILED" "$RC" "$START_TS" "$END_TS" "$CFG_DIR" "$DETAIL"
    printf '[supplementary] FAILED    %s exit_code=%s (%s)\n' "$CFG_ID" "$RC" "$DETAIL"
    N_FAILED=$((N_FAILED + 1))
    OVERALL=1
  fi
done

printf '[supplementary] summary: complete=%s skipped=%s failed=%s blocked=%s; records: %s\n' \
  "$N_COMPLETE" "$N_SKIPPED" "$N_FAILED" "$N_BLOCKED" "$STATUS_TSV"

if [ "$OVERALL" -eq 0 ]; then
  if [ "$MATRIX_ONLY_SET" = 1 ]; then
    printf '[supplementary] result: selected configuration %s is COMPLETE or SKIPPED_ALREADY_COMPLETE (operational completion of the selected configuration only, not scientific validation); the remaining 3 supplementary configurations were not executed by this invocation and remain NOT_RUN for the independent checker\n' "$RACELOOM_MATRIX_ONLY"
  else
    printf '[supplementary] result: all 4 configurations are COMPLETE or SKIPPED_ALREADY_COMPLETE (operational completion only, not scientific validation)\n'
  fi
else
  printf '[supplementary] result: at least one configuration FAILED or is BLOCKED; inspect %s\n' "$STATUS_TSV"
fi

exit "$OVERALL"
