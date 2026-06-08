# Artifact review guide

This repository contains benchmark inputs and helper scripts for RaceLoom. It does not include RaceLoom itself. RaceLoom should be obtained from the RaceLoom artifact record on Zenodo:

https://doi.org/10.5281/zenodo.16884345

## Quick start: Ubuntu / Linux amd64

```bash
git clone https://github.com/sarmadiali98/RaceLoom-Bench.git
cd RaceLoom-Bench

bash scripts/setup_raceloom_artifact.sh

export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
export RACELOOM_CMD="python main.py"

bash scripts/docker_smoke_test.sh
Quick start: macOS with Docker Desktop or Colima

On Intel Macs, the Ubuntu/Linux commands should work directly.

On Apple Silicon Macs, use the amd64 platform flag if the RaceLoom image is provided only for linux/amd64:

git clone https://github.com/sarmadiali98/RaceLoom-Bench.git
cd RaceLoom-Bench

bash scripts/setup_raceloom_artifact.sh

export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
export RACELOOM_CMD="python main.py"
export DOCKER_PLATFORM=linux/amd64

bash scripts/docker_smoke_test.sh

Apple Silicon runs through emulation in this mode. It is suitable for smoke testing, but runtimes are not representative of native Linux/amd64 execution.

Reviewer smoke test

The default smoke test runs a small B2 route-mapping benchmark pair.

bash scripts/docker_smoke_test.sh

Expected result:

Model	Generated traces	Harmful races
B2 smoke faulty	8	1
B2 smoke control	8	0

A successful run ends with:

PASS
bad:     traces=8 harmful=1
control: traces=8 harmful=0
Full benchmark reruns

The full B1--B4 and S1--S4 benchmark suites can take substantially longer than the smoke test. They are intended for a native Ubuntu/Linux amd64 machine or a comparable workstation/server.

Reference summaries are available in:

docs/final_4x4_matrix.md
docs/final_4x4_matrix.tsv
docs/synthetic_s1_s4_matrix.md
docs/synthetic_s1_s4_matrix.tsv

