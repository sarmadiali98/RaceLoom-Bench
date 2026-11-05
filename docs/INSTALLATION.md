# Installation

This document describes how to install everything needed to execute and validate the RaceLoom-Bench artifact. For the reviewer walkthrough start at `ARTIFACT.md`; for execution see `docs/REPRODUCTION.md`; for the independent checkers see `docs/VALIDATION.md`.

## Hardware requirements

### Reference reproduction hardware

The verified reference reproduction of all 20 baseline-backed configurations (2026-11-04, canonical pipeline) ran on this machine (verified independently during release preparation):

| Item | Value |
|---|---|
| Architecture | x86_64 (linux/amd64) |
| CPU | Intel(R) Core(TM) i5-8500 CPU @ 3.00GHz |
| Logical CPUs | 6 |
| RAM | 30 GiB |
| Operating system | Ubuntu 26.04.1 LTS (as currently reported by the reproduction host) |
| Docker | 29.1.3 (client and server) |
| Disk available during the reported runs | ~670 GB |

For comparison, the earlier 2026-06 historical validation (whose sanitized logs ship with this artifact) ran on a larger 64-core Intel Xeon Gold 6230 server with 126 GiB RAM under Ubuntu 24.04.3 LTS.

### Recommended reviewer hardware

- **Smoke test and individual benchmark configurations:** a laptop is usually sufficient, depending on its specifications. The smoke test needs a Docker-capable machine with ~3 GB free disk and finishes in about a minute on native amd64 hardware. A single configuration runs between ~5 minutes (B2_K8_T1_atlanta) and ~1 hour (B4_K16_T4_germany50) on the reference machine.
- **Complete reproduction:** use hardware comparable to or better than the reference reproduction machine — approximately 6 logical CPUs and 30 GiB RAM. This is a practical recommendation derived from the machine that actually performed the verified reproduction; it has not been tested as a scientifically established minimum.
- **Laptop warning:** running the complete benchmark suite on an ordinary laptop may be considerably slower and can encounter CPU, memory, or thermal limitations. If you only have a laptop, run the smoke test and individual benchmarks first; they demonstrate the pipeline end-to-end without the multi-hour commitment.
- **Disk space:** ~795 MB for the RaceLoom archive download, ~2.0 GB for the loaded Docker image, and under 100 MB for all generated evidence (the reference principal-matrix evidence root is ~61 MiB, the supplementary root ~9 MiB; harmful-trace artifacts dominate). Budget a few GB in total.
- **GPU:** not required and not used; RaceLoom is CPU-only.

### Operating system and Docker requirements

| Requirement | Value |
|---|---|
| Operating system | Native Linux amd64 (recommended; the reference reproduction host runs Ubuntu 26.04.1 LTS — any recent Linux amd64 distribution with Docker is suitable). macOS works through Docker Desktop or Colima; on Apple Silicon the container runs emulated as `linux/amd64`, which is suitable for the smoke test and individual benchmarks but not for representative runtimes. |
| Container runtime | Docker (any recent release; the reference host used Docker 29.1.3 client and server). |
| Network | Required once to download the RaceLoom artifact archive from Zenodo (~795 MB). Benchmark execution itself needs no network access: the pipeline uses only the local image and bind mounts. |

### Expected execution times

All figures below are recorded wall-clock measurements of specific runs on the reference machine (see `docs/RESULTS.md` and `docs/runtime_summary.md`); they are measurements, not guarantees, and are never used as reproducibility criteria.

| Workload | Recorded duration |
|---|---|
| Smoke test (both sides, RaceLoom execution time) | ~1.2 s + ~1.2 s; end-to-end under a minute |
| Fastest single configuration (B2_K8_T1_atlanta, both sides) | ~5.3 min |
| Slowest single configuration (B4_K16_T4_germany50, both sides) | ~60.3 min |
| Complete principal matrix (16 configurations) | ~6.8 h (2026-11-04, 09:47–16:34 UTC) |
| Complete supplementary group (4 configurations) | ~1.3 h (2026-11-04, 17:06–18:23 UTC) |

RaceLoom is primarily single-threaded per run, so smaller machines execute the same configurations with proportionally longer wall-clock times.

## Docker installation assumptions

The artifact-review path assumes a working `docker` executable in `PATH` with permission to run containers and bind-mount host directories.

- **Ubuntu**: a standard `docker-ce` installation from the Docker repository (see the "Installing Docker" section of the top-level `README.md` for the full command sequence). Verify with `docker run hello-world`.
- **macOS**: Docker Desktop, or Colima (`brew install docker colima && colima start`). On Apple Silicon, export `DOCKER_PLATFORM=linux/amd64` if the RaceLoom image is provided only for `linux/amd64`.

## Runtime acquisition from Zenodo

RaceLoom itself is distributed separately from this repository, as a Docker image archive attached to the RaceLoom artifact record:

- Artifact DOI: <https://doi.org/10.5281/zenodo.16884345>
- Direct download: <https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1>

The helper script downloads the archive, verifies it, loads it, and verifies the loaded image identity:

```bash
bash scripts/setup_raceloom_artifact.sh
```

The script verifies the archive size (794,997,198 bytes) and SHA-256 (`bc533c637a0fa55e51f6c84c07137bdd44ddbd303c9a2443ab6301710ec58d45`) **before** loading, refuses to load a mismatched archive, and after loading verifies that the image ID equals the pinned reference reproduction image. It can be rerun safely: an existing, checksum-valid archive is reused instead of re-downloaded. To perform the same steps manually:

```bash
curl -L "https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1" -o raceloom.tar.gz
sha256sum raceloom.tar.gz        # must print bc533c63...58d45
gunzip -c raceloom.tar.gz | docker load
```

Never load or execute an archive that failed verification.

## Image identity verification

The reference reproductions for this release used the pinned local image ID

```text
sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087
```

with architecture `amd64`. After loading, verify the local image identity:

```bash
docker image inspect raceloom:latest --format '{{.Id}} {{.Architecture}}'
```

**Verified correspondence (2026-11-05):** the published Zenodo archive `raceloom.tar.gz` (SHA-256 `bc533c63…58d45`, 794,997,198 bytes) was checked in an isolated Docker environment: loading it produces exactly the pinned image ID `sha256:fe13627b…` with architecture `amd64`. The archive's image configuration also matches the pinned image's filesystem layers exactly (all 20 `rootfs.diff_ids` in order) and its runtime configuration (Python 3.12.11, environment, entrypoint).

A Docker image ID is the content address of the local image config, so a different ID can in principle still be the same distribution content — but this artifact never silently accepts a different image: `scripts/setup_raceloom_artifact.sh` fails on a mismatch, and `scripts/verify_environment.sh` reports `FAIL image ID mismatch` unless `RACELOOM_EXPECTED_IMAGE_ID` is explicitly set (only after independently establishing that a different image is correct). The canonical launchers additionally record the requested image reference and the resolved image ID in every per-configuration `provenance.tsv`, so the runtime identity of any execution is always captured in the evidence.

## Required command-line tools

| Tool | Used for |
|---|---|
| `bash` | All execution scripts. |
| `docker` | Container execution. |
| `curl` | One-time RaceLoom archive download. |
| `gunzip` | One-time archive decompression. |
| `git` | Repository clone and integrity checks. |
| `python3` | Checkers, test suites, and log-extraction helpers. |
| `sha256sum` (Linux) or `shasum -a 256` (macOS) | Checksum verification. |

`bash scripts/verify_environment.sh` checks all of these in one command and reports one `PASS`/`FAIL` line per requirement.

## Python requirements

Execution and validation use the **Python 3 standard library only**. The independent checkers (`scripts/check_final_matrix.py`, `scripts/check_supplementary_matrix.py`), their test suites, and the log-extraction helpers import nothing beyond the standard library, so no `pip` installation is required. Any recent Python 3 release works; the reference validation host used Python 3.13.5 (historical validation) and Python 3.14.4 (reproduction provenance recording).

## Installation verification

With the environment configured:

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
bash scripts/verify_environment.sh
```

A complete environment ends with `verify_environment: OK` (exit code 0).

Then run the smoke test:

```bash
bash scripts/docker_smoke_test.sh
```

A successful installation ends with:

```text
SMOKE TEST: PASS
```

This runs the small B2 route-mapping smoke pair at depth 4 with BFS through the canonical pipeline inside the RaceLoom container and checks the exact expected outcome (8 traces / 1 faulty harmful race / 0 control harmful races, branch signature `CRoute:1;BSw:2`). It is the fastest end-to-end proof that Docker, the RaceLoom image, and the repository scripts work together. Expected wall-clock time is under a minute on native amd64 hardware (the reference macOS/Colima emulated run took ~33 s total).
