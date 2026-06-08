#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'
This script is kept only as a compatibility placeholder.

For artifact-review execution, use the Docker-based scripts instead:

  export RACELOOM_IMAGE=<raceLoom-image>:<tag>
  bash scripts/docker_smoke_test.sh

or:

  bash scripts/docker_run_pair.sh <benchmark-pair-dir> <depth> <output-dir> [strategy]

RaceLoom itself is distributed separately from this benchmark repository.
EOF

exit 2
