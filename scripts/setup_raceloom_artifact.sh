#!/usr/bin/env bash
set -euo pipefail

# Download, verify, and load the external RaceLoom Docker runtime image.
#
# RaceLoom is distributed separately from RaceLoom-Bench as a Docker image
# archive attached to the RaceLoom artifact record (Zenodo DOI 10.5281/zenodo.16884345).
# This script:
#   1. obtains raceloom.tar.gz (skipping the download when a valid copy exists),
#   2. verifies the archive SHA-256 against the checksum recorded for this release,
#   3. loads it into the local Docker image store,
#   4. verifies that the loaded image ID equals the pinned image ID used for the
#      reference reproductions, and refuses to report success otherwise.
#
# The pinned identity is never silently bypassed: set RACELOOM_EXPECTED_IMAGE_ID
# only if you have independently established that a different image is correct.

RACELOOM_ARTIFACT_URL="https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1"
# An explicitly provided archive path belongs to the reviewer and is never
# deleted or overwritten by this script.
ARCHIVE_EXPLICIT=0
if [ "${RACELOOM_ARCHIVE+x}" = x ] && [ -n "$RACELOOM_ARCHIVE" ]; then
  ARCHIVE_EXPLICIT=1
fi
RACELOOM_ARCHIVE="${RACELOOM_ARCHIVE:-raceloom.tar.gz}"
EXPECTED_ARCHIVE_SHA256="bc533c637a0fa55e51f6c84c07137bdd44ddbd303c9a2443ab6301710ec58d45"
EXPECTED_ARCHIVE_SIZE="794997198"
EXPECTED_IMAGE_TAG="raceloom:latest"
EXPECTED_IMAGE_ID="${RACELOOM_EXPECTED_IMAGE_ID:-sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087}"

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

detect_sha256() {
  if command -v sha256sum >/dev/null 2>&1 && sha256sum /dev/null >/dev/null 2>&1; then
    SHA256_TOOL="sha256sum"
  elif command -v shasum >/dev/null 2>&1 && shasum -a 256 /dev/null >/dev/null 2>&1; then
    SHA256_TOOL="shasum -a 256"
  else
    die "no SHA-256 utility available (tried 'sha256sum' and 'shasum -a 256'); archive verification requires SHA-256"
  fi
}

archive_sha256() {
  case "$SHA256_TOOL" in
    sha256sum) sha256sum -- "$1" | awk '{print $1}' ;;
    "shasum -a 256") shasum -a 256 -- "$1" | awk '{print $1}' ;;
    *) return 1 ;;
  esac
}

command -v curl >/dev/null 2>&1 || die "curl not found in PATH; install curl and retry"
command -v docker >/dev/null 2>&1 || die "docker not found in PATH; install/start Docker and retry"
docker info >/dev/null 2>&1 || die "docker daemon not accessible; start Docker and retry"
detect_sha256

verify_archive() {
  local actual_size actual_hash
  actual_size="$(wc -c < "$RACELOOM_ARCHIVE" | tr -d '[:space:]')"
  if [ "$actual_size" != "$EXPECTED_ARCHIVE_SIZE" ]; then
    printf 'archive size mismatch: expected %s bytes, got %s bytes\n' "$EXPECTED_ARCHIVE_SIZE" "$actual_size" >&2
    return 1
  fi
  actual_hash="$(archive_sha256 "$RACELOOM_ARCHIVE")" || die "cannot compute SHA-256 of $RACELOOM_ARCHIVE"
  if [ "$actual_hash" != "$EXPECTED_ARCHIVE_SHA256" ]; then
    printf 'archive SHA-256 mismatch:\n  expected: %s\n  observed: %s\n' "$EXPECTED_ARCHIVE_SHA256" "$actual_hash" >&2
    return 1
  fi
  return 0
}

if [ -f "$RACELOOM_ARCHIVE" ]; then
  echo "Found existing archive: $RACELOOM_ARCHIVE"
  echo "Verifying against the release checksum..."
  if verify_archive; then
    echo "Archive checksum verified; skipping download."
  else
    if [ "$ARCHIVE_EXPLICIT" = "1" ]; then
      die "existing archive $RACELOOM_ARCHIVE does not match the release checksum; move it away or point RACELOOM_ARCHIVE at the correct file (do not reuse a mismatched archive)"
    fi
    echo "Existing archive does not match the release checksum; re-downloading..."
    rm -f "$RACELOOM_ARCHIVE"
  fi
fi

if [ ! -f "$RACELOOM_ARCHIVE" ]; then
  echo "Downloading RaceLoom Docker artifact from Zenodo..."
  echo "URL: $RACELOOM_ARTIFACT_URL"
  curl -L "$RACELOOM_ARTIFACT_URL" -o "$RACELOOM_ARCHIVE"
  echo
  echo "Verifying archive size and SHA-256..."
  verify_archive || die "downloaded archive failed verification; do not load it; retry the download or check your network/proxy"
  echo "Archive verified: size ${EXPECTED_ARCHIVE_SIZE} bytes, SHA-256 ${EXPECTED_ARCHIVE_SHA256}"
fi

echo
echo "Loading RaceLoom Docker image..."
gunzip -c "$RACELOOM_ARCHIVE" | docker load

LOADED_ID="$(docker image inspect --format '{{.Id}}' "$EXPECTED_IMAGE_TAG" 2>/dev/null)" \
  || die "image $EXPECTED_IMAGE_TAG not found after loading; inspect 'docker images' output above"
LOADED_ARCH="$(docker image inspect --format '{{.Architecture}}' "$EXPECTED_IMAGE_TAG" 2>/dev/null || printf 'unknown')"

echo
echo "Loaded image: $EXPECTED_IMAGE_TAG"
echo "  image ID:       $LOADED_ID"
echo "  architecture:   $LOADED_ARCH"

if [ "$LOADED_ID" != "$EXPECTED_IMAGE_ID" ]; then
  printf 'ERROR: loaded image ID does not match the pinned runtime identity of this release.\n  expected: %s\n  loaded:   %s\nThe benchmark instructions must never silently accept a different image.\nIf you have independently established that the different image is correct, re-run with:\n  RACELOOM_EXPECTED_IMAGE_ID=%s bash scripts/setup_raceloom_artifact.sh\nand record the image you actually executed with.\n' \
    "$EXPECTED_IMAGE_ID" "$LOADED_ID" "$LOADED_ID" >&2
  exit 1
fi
echo "  identity check: OK (matches the pinned reference reproduction image)"

echo
echo "Available RaceLoom images:"
docker images --format '{{.Repository}}:{{.Tag}}  {{.ID}}' | grep -i raceloom || true

cat <<'EOF'

RaceLoom artifact setup finished.

For the benchmark scripts, use:

  export RACELOOM_IMAGE=raceloom:latest
  export RACELOOM_WORKDIR=/raceloom

On Apple Silicon Macs, also use:

  export DOCKER_PLATFORM=linux/amd64

Then verify your environment and run the smoke test:

  bash scripts/verify_environment.sh
  bash scripts/docker_smoke_test.sh
EOF
