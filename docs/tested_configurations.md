# Tested configurations

This file records the systems used to generate and check the benchmark results.

## Full benchmark generation / validation server

| Item | Value |
|---|---|
| OS | Ubuntu 24.04.3 LTS |
| Kernel | Linux 6.8.0-87-generic x86_64 |
| Memory | approximately 128 GB RAM |
| RaceLoom execution | RaceLoom artifact environment with KATch |
| Strategy | BFS |

The main B1--B4 matrix is recorded in `docs/final_4x4_matrix.md`.
The synthetic S1--S4 matrix is recorded in `docs/synthetic_s1_s4_matrix.md`.

## Reviewer smoke test on macOS / Colima

This test checked that a fresh clone of `RaceLoom-Bench` can be mounted into the RaceLoom Docker image and executed through the reviewer-facing wrapper scripts.

| Item | Value |
|---|---|
| Host | macOS on Apple Silicon |
| Docker runtime | Colima |
| Docker client | 29.4.3 |
| Docker server | 29.2.1 |
| Container platform | `linux/amd64` |
| RaceLoom image used for local test | `raceloom:latest` |
| RaceLoom workdir | `/raceloom` |
| Test directory | fresh clone under the user's home directory |

Command used:

    git clone https://github.com/sarmadiali98/RaceLoom-Bench.git RaceLoom-Bench-review-test
    cd RaceLoom-Bench-review-test

    export RACELOOM_IMAGE=raceloom:latest
    export RACELOOM_WORKDIR=/raceloom
    export RACELOOM_CMD="python main.py"
    export DOCKER_PLATFORM=linux/amd64

    time bash scripts/docker_smoke_test.sh

Expected result:

| Benchmark | Model | Generated traces | Harmful races | RaceLoom time |
|---|---|---:|---:|---:|
| B2 route-mapping smoke | faulty | 8 | 1 | 15.49s |
| B2 route-mapping smoke | control | 8 | 0 | 15.68s |

Total wall-clock time: 36.774s.

Apple Silicon uses amd64 emulation for this image, so this runtime is only a smoke-test reference. Full benchmark runtimes should be measured on native Linux/amd64.
