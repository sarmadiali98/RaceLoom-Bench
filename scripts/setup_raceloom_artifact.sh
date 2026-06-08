#!/usr/bin/env bash
set -euo pipefail

RACELOOM_ARTIFACT_URL="https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1"
RACELOOM_ARCHIVE="${RACELOOM_ARCHIVE:-raceloom.tar.gz}"

echo "Downloading RaceLoom Docker artifact from Zenodo..."
echo "URL: $RACELOOM_ARTIFACT_URL"
echo

curl -L "$RACELOOM_ARTIFACT_URL" -o "$RACELOOM_ARCHIVE"

echo
echo "Loading RaceLoom Docker image..."
gunzip -c "$RACELOOM_ARCHIVE" | docker load

echo
echo "Available RaceLoom images:"
docker images | grep -i raceloom || true

cat <<'EOF'

RaceLoom artifact setup finished.

For the benchmark scripts, use:

  export RACELOOM_IMAGE=raceloom:latest
  export RACELOOM_WORKDIR=/raceloom
  export RACELOOM_CMD="python main.py"

On Apple Silicon Macs, also use:

  export DOCKER_PLATFORM=linux/amd64

Then run:

  bash scripts/docker_smoke_test.sh
EOF
