#!/usr/bin/env bash
# Reviewer environment preflight for RaceLoom-Bench.
#
# One command that checks everything needed before committing time to the
# smoke test or a benchmark reproduction. Prints one PASS/FAIL/WARN line per
# check and a final verdict; exits nonzero when a required check fails.
#
# Usage:
#   bash scripts/verify_environment.sh [--image IMAGE] [--skip-checksums]
#                                      [--no-image-id-check]
#
# Exit codes: 0 = all required checks pass, 1 = at least one required check
# failed, 2 = usage error.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT" || exit 2

IMAGE="${RACELOOM_IMAGE:-}"
SKIP_CHECKSUMS=0
NO_IMAGE_ID_CHECK=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --image)
      [ "$#" -ge 2 ] || { printf 'ERROR: --image requires a value\n' >&2; exit 2; }
      IMAGE="$2"; shift 2 ;;
    --skip-checksums) SKIP_CHECKSUMS=1; shift ;;
    --no-image-id-check) NO_IMAGE_ID_CHECK=1; shift ;;
    -h|--help)
      sed -n '2,12p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *) printf 'ERROR: unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done

# Pinned runtime identity of this release (see provenance/runtime.txt).
PINNED_IMAGE_ID="sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087"
PINNED_IMAGE_ID="${RACELOOM_EXPECTED_IMAGE_ID:-$PINNED_IMAGE_ID}"

FAILURES=0

pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; FAILURES=$((FAILURES + 1)); }
warn() { printf 'WARN %s\n' "$1"; }

# --- host tools -------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  pass "python3 ($(python3 -c 'import sys; sys.stdout.write("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || printf 'version unknown'))"
else
  fail "python3 (required by the independent checkers and their test suites)"
fi

command -v git >/dev/null 2>&1 && pass "git" || fail "git (repository clone and integrity checks)"

if command -v curl >/dev/null 2>&1; then
  pass "curl (one-time RaceLoom archive download)"
else
  warn "curl (needed only by scripts/setup_raceloom_artifact.sh; skip if the archive is already loaded)"
fi

SHA256_TOOL=""
if command -v sha256sum >/dev/null 2>&1 && sha256sum /dev/null >/dev/null 2>&1; then
  SHA256_TOOL="sha256sum"
elif command -v shasum >/dev/null 2>&1 && shasum -a 256 /dev/null >/dev/null 2>&1; then
  SHA256_TOOL="shasum -a 256"
fi
if [ -n "$SHA256_TOOL" ]; then
  pass "sha256 tool ($SHA256_TOOL)"
else
  fail "sha256 tool (tried 'sha256sum' and 'shasum -a 256'; required for checksum verification)"
fi

# --- Docker -----------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
  pass "docker executable ($(docker --version 2>/dev/null | sed 's/^Docker version //; s/, build .*//'))"
else
  fail "docker executable (install Docker: https://docs.docker.com/get-docker/)"
fi

if docker info >/dev/null 2>&1; then
  pass "docker daemon reachable (server $(docker version --format '{{.Server.Version}}' 2>/dev/null || printf 'version unknown'))"
else
  fail "docker daemon reachable (start Docker Desktop / the docker service, then retry)"
fi

# --- RaceLoom image ---------------------------------------------------------
if [ -z "$IMAGE" ]; then
  warn "RACELOOM_IMAGE not set and --image not given; skipping image checks (set it to raceloom:latest after scripts/setup_raceloom_artifact.sh)"
else
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    pass "RaceLoom image present ($IMAGE)"
    IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null)"
    IMAGE_ARCH="$(docker image inspect --format '{{.Architecture}}' "$IMAGE" 2>/dev/null)"
    pass "image identity (id: ${IMAGE_ID:-unknown}, architecture: ${IMAGE_ARCH:-unknown})"
    if [ "$NO_IMAGE_ID_CHECK" = "0" ]; then
      if [ "$IMAGE_ID" = "$PINNED_IMAGE_ID" ]; then
        pass "image ID matches the pinned reference reproduction image"
      else
        fail "image ID mismatch: expected ${PINNED_IMAGE_ID}, found ${IMAGE_ID:-unknown}.
     The reference reproductions ran with the pinned image; a different image is
     never silently accepted. Load the published archive with
     scripts/setup_raceloom_artifact.sh, or, only after independently
     establishing that a different image is correct, re-run with
     RACELOOM_EXPECTED_IMAGE_ID=<id> set."
      fi
    fi
    if [ -n "$IMAGE_ARCH" ] && [ "$IMAGE_ARCH" != "amd64" ]; then
      warn "image architecture is ${IMAGE_ARCH}, not amd64; emulated execution is suitable for smoke testing but runtimes are not representative (see docs/INSTALLATION.md)"
    fi
  else
    fail "RaceLoom image present ($IMAGE not found locally; run scripts/setup_raceloom_artifact.sh)"
  fi
fi

# --- release checksum manifest ---------------------------------------------
if [ "$SKIP_CHECKSUMS" = "1" ]; then
  warn "checksum manifest verification skipped (--skip-checksums)"
elif [ -n "$SHA256_TOOL" ] && [ -f "provenance/checksums.sha256" ]; then
  if [ "$SHA256_TOOL" = "sha256sum" ]; then
    CHECK_OUT="$(sha256sum -c provenance/checksums.sha256 2>&1)" && CHECK_RC=0 || CHECK_RC=$?
  else
    CHECK_OUT="$(shasum -a 256 -c provenance/checksums.sha256 2>&1)" && CHECK_RC=0 || CHECK_RC=$?
  fi
  if [ "$CHECK_RC" -eq 0 ]; then
    pass "release checksum manifest ($(printf '%s\n' "$CHECK_OUT" | grep -c ': OK$') files OK)"
  else
    fail "release checksum manifest: some release-critical files are missing or modified:
$(printf '%s\n' "$CHECK_OUT" | grep -v ': OK$' | sed 's/^/     /')"
  fi
else
  warn "checksum manifest verification skipped (no SHA-256 tool or provenance/checksums.sha256 not found)"
fi

if [ "$FAILURES" -eq 0 ]; then
  echo "verify_environment: OK"
  exit 0
fi
echo "verify_environment: FAILURES PRESENT ($FAILURES)"
exit 1
