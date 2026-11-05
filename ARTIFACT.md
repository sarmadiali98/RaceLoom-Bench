# RaceLoom-Bench Artifact Quick Start

This is the reviewer-facing entry point for the RaceLoom-Bench artifact. It
gives the shortest verified path from a clean machine to a reproduced,
independently validated result, and it assumes **no prior knowledge** of
RaceLoom, this repository, or the benchmark naming. For the conceptual
overview and the scientific scope, read [`README.md`](README.md); the
detailed references are [`docs/INSTALLATION.md`](docs/INSTALLATION.md),
[`docs/REPRODUCTION.md`](docs/REPRODUCTION.md),
[`docs/VALIDATION.md`](docs/VALIDATION.md), and
[`docs/RESULTS.md`](docs/RESULTS.md).

## What this artifact is, in one paragraph

RaceLoom-Bench is a benchmark suite for RaceLoom, a model checker for
software-defined networking race conditions. Each benchmark is a *pair*: a
**faulty** model (`bad/`) that seeds one realistic SDN fault, and a **control**
model (`control/`) that is identical except for that fault. A correct tool
must find harmful races on the faulty side and zero on the control side. The
repository contains the benchmark models, the properties they are checked
against, the execution pipeline, and two independent checkers that verify
fresh results against recorded historical expectations. RaceLoom itself is
**not** in this repository: it is distributed as a Docker image through its
own artifact record (Zenodo DOI [10.5281/zenodo.16884345](https://doi.org/10.5281/zenodo.16884345)),
which you download, verify, and load once.

Everything runs in Docker; you do not need to install or understand anything
about RaceLoom, Maude, or KATch.

## Hardware requirements

The verified reference reproduction (all 20 baseline-backed configurations,
2026-11-04) ran on this machine:

| Item | Reference value |
|---|---|
| Architecture | x86_64 (linux/amd64) |
| CPU | Intel Core i5-8500 @ 3.00 GHz, 6 logical CPUs |
| RAM | 30 GiB |
| OS | Ubuntu 26.04.1 LTS |
| Docker | 29.1.3 |
| Disk available | ~670 GB |

**Recommendations for reviewers:**

- **Smoke test and individual benchmarks:** a laptop is usually sufficient.
  The smoke test needs a Docker-capable machine with ~3 GB free disk and
  finishes in about a minute on native amd64 hardware. A single benchmark
  configuration runs between ~5 minutes (B2_K8_T1_atlanta) and ~1 hour
  (B4_K16_T4_germany50) on the reference machine.
- **Complete reproduction:** use hardware comparable to or better than the
  reference machine (approximately 6 logical CPUs and 30 GiB RAM). This is a
  practical recommendation from the machine that actually performed the
  verified reproduction, not a scientifically established minimum.
- **Laptop warning:** running the complete benchmark suite on an ordinary
  laptop can be considerably slower and may hit CPU, memory, or thermal
  limits. If you only have a laptop, run the smoke test and individual
  benchmarks first; they demonstrate the pipeline end-to-end.
- **Disk:** budget ~3 GB for the runtime archive and loaded image, plus under
  100 MB for all generated evidence (the reference principal-matrix evidence
  root is ~61 MiB and the supplementary root ~9 MiB).
- **GPU:** not required and not used. RaceLoom is CPU-only.
- **OS and Docker:** any recent Linux amd64 distribution with a recent Docker
  is suitable. macOS works through Docker Desktop or Colima; on Apple Silicon
  the container runs emulated as `linux/amd64`, which is suitable for the
  smoke test and individual benchmarks but not for representative timings.

**Expected execution times** (recorded wall-clock measurements on the
reference machine, not guarantees — timing is never a scientific criterion):

| Workload | Recorded duration |
|---|---|
| Smoke test | < 1 minute (RaceLoom itself: ~1.2 s per side) |
| Fastest single configuration (B2_K8_T1_atlanta) | ~5.3 min (both sides) |
| Slowest single configuration (B4_K16_T4_germany50) | ~60.3 min (both sides) |
| Complete principal matrix (16 configurations) | ~6.8 h (09:47–16:34 UTC) |
| Complete supplementary group (4 configurations) | ~1.3 h (17:06–18:23 UTC) |

## The benchmarks, named

You do not need to know these names in advance — every command below uses
them verbatim — but here is what they mean:

- **B1–B4** are the four *benchmark families*: B1 waypoint/IDS-bypass, B2
  wrong next-hop/route mapping, B3 slice isolation, B4 failover/stale path.
- **T1–T4** are the four *topologies* the families are embedded in: T1
  Atlanta (K8), T2 Nobel-EU (K12), T3 Geant2012 (K14), T4 Germany50 (K16).
  The K-number is the topology size parameter of that embedding.
- A *principal configuration* is one family on one topology, e.g.
  `B2_K14_T3_geant2012` = family B2, topology T3 at K14. There are 16.
- **S1–S4** are four additional *synthetic* configurations (fixed synthetic
  scenarios, not embedded in the SNDlib/TopoHub topologies), e.g.
  `S1_multidomain_wrong_destination`.
- The *smoke benchmark* is a miniature B2 pair (`b2_route_mapping_smoke`) on
  T1 Atlanta used only to check your installation; it is not part of the
  20 baseline-backed scientific configurations.

## Step 1 — Obtain the artifact

```bash
git clone https://github.com/sarmadiali98/RaceLoom-Bench.git
cd RaceLoom-Bench
```

(If you received a release archive instead, extract it and `cd` into the
extracted `RaceLoom-Bench` directory.)

Verify that the release-critical files are intact:

```bash
sha256sum -c provenance/checksums.sha256        # Linux
shasum -a 256 -c provenance/checksums.sha256    # macOS
```

**Success:** every line ends with `: OK`, exit code 0.

## Step 2 — Install Docker

Install Docker Desktop (macOS/Windows) or Docker Engine (Linux) following the
official guide: <https://docs.docker.com/get-docker/>. On Ubuntu, the
"Installing Docker" section of [`README.md`](README.md) has the full command
sequence. Then confirm:

```bash
docker --version
docker run hello-world
```

**Success:** a version line, then Docker's welcome message.

## Step 3 — Obtain the runtime image

This downloads the RaceLoom Docker image archive (~795 MB) from Zenodo,
verifies its SHA-256 against the checksum recorded for this release, loads it
into Docker, and verifies that the loaded image ID equals the pinned image ID
used for the reference reproductions:

```bash
bash scripts/setup_raceloom_artifact.sh
```

**Success:** the script prints `Archive verified: ...`, `Loaded image:
raceloom:latest`, `identity check: OK (matches the pinned reference
reproduction image)`, and `RaceLoom artifact setup finished.` Exit code 0.

The archive is kept as `raceloom.tar.gz` in the current directory; rerunning
the script re-verifies it and skips the download. A checksum or image-ID
mismatch is a hard error — a different image is never silently accepted.

## Step 4 — Verify the environment

One command that checks every prerequisite (Docker, the image and its
identity, Python 3, the SHA-256 tool, and the release checksum manifest):

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
bash scripts/verify_environment.sh
```

**Success:** one `PASS ...` line per check and a final
`verify_environment: OK`, exit code 0.

On Apple Silicon Macs, also `export DOCKER_PLATFORM=linux/amd64` (used by all
execution commands below).

## Step 5 — Run the smoke test

```bash
bash scripts/docker_smoke_test.sh
```

This runs the miniature B2 pair through the same canonical pipeline the full
reproduction uses — faulty side first, then control — and independently
checks the exact expected outcome. Expected wall-clock time is under a minute
on native amd64 hardware.

**Success:** the run ends with

```text
PASS
bad:     traces=8 harmful=1 branches=CRoute:1;BSw:2 total=...
control: traces=8 harmful=0 branches=CRoute:1;BSw:2 total=...

SMOKE TEST: PASS
```

and exit code 0. **Output location:** everything is written under
`~/raceloom-bench-smoke/smoke_<timestamp>/` (override with
`--output-root DIR`): `console/` holds both console logs, `artifacts/bad/`
and `artifacts/control/` hold each side's persisted RaceLoom run artifacts
(`final_stats.csv`, `run_*/harmful_traces/`). Each run gets a fresh
directory; previous evidence is never overwritten.

**Failure:** `SMOKE TEST: FAIL` with the reason, exit code 1; environment
problems (Docker missing, image missing) exit 2 with instructions. See
[Troubleshooting](#troubleshooting).

## Step 6 — Run an individual benchmark

You do not need to run all 20 configurations to try one experiment. Set
`RACELOOM_MATRIX_ONLY` to exactly one configuration ID:

```bash
# One principal configuration (any of B1/B2/B3/B4 x K8/K12/K14/K16):
export RACELOOM_MATRIX_OUTPUT_ROOT="$HOME/raceloom-bench-evidence"
mkdir -p "$RACELOOM_MATRIX_OUTPUT_ROOT"
RACELOOM_MATRIX_ONLY=B2_K8_T1_atlanta bash scripts/run_final_matrix.sh

# One supplementary configuration (any of S1-S4):
RACELOOM_MATRIX_ONLY=S1_multidomain_wrong_destination bash scripts/run_supplementary_matrix.sh
```

The value must match one configuration ID exactly; empty, comma-separated,
glob-like, path-like, or unknown values abort before anything runs — a
selection can never accidentally trigger the full matrix. Both sides run in
the established order (faulty first), with full provenance records, console
logs, persisted artifacts, and the same resume/locking behavior as the full
matrix.

**Success:** `[matrix] COMPLETE B2_K8_T1_atlanta` (or
`[supplementary] COMPLETE ...`), exit code 0. Exit 0 in selection mode means
the *selected configuration* completed operationally; it does not mean the
full matrix was reproduced.

**Output location:** `$RACELOOM_MATRIX_OUTPUT_ROOT/<CONFIG_ID>/` with
`console/`, `artifacts/`, `provenance.tsv`, and `STATUS_COMPLETE`; a root
`status.tsv` records the attempt. Reusing the same output root later skips
completed configurations and continues with the rest.

## Step 7 — Run the complete reproduction

The complete baseline-backed reproduction is the 16 principal configurations
plus the 4 supplementary configurations (about 8 h total on the reference
machine; resumable, so it can be interrupted and continued):

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_MATRIX_OUTPUT_ROOT="$HOME/raceloom-bench-evidence"
mkdir -p "$RACELOOM_MATRIX_OUTPUT_ROOT"

bash scripts/run_final_matrix.sh            # principal 16-configuration matrix (~6.8 h)
bash scripts/run_supplementary_matrix.sh    # supplementary S1-S4 group (~1.3 h)
```

**Success:** each launcher ends with `result: all 16 configurations are
COMPLETE or SKIPPED_ALREADY_COMPLETE` (respectively `all 4 configurations`),
exit code 0. These are operational completions; scientific validation is the
next step. If a configuration fails, it is reported `BLOCKED` or `FAILED` and
is never rerun automatically; inspect `status.tsv` and the configuration's
evidence directory.

The four smoke configurations in `benchmarks/smoke/` have no historical
baselines and are **not** part of this reproduction or its scientific claims.

## Step 8 — Validate the results

Two independent, read-only checkers compare the fresh evidence against the
committed historical expectations (trace counts, harmful-race counts, branch
signatures, depths, strategies, and cache counters; timing is recorded but
never judged):

```bash
python3 scripts/check_final_matrix.py --matrix-root "$RACELOOM_MATRIX_OUTPUT_ROOT"
python3 scripts/check_supplementary_matrix.py --matrix-root "$RACELOOM_MATRIX_OUTPUT_ROOT"
```

**Success:** when the complete baseline-backed suite was reproduced
correctly, the principal checker reports `OVERALL: PASS` with **16/16
configurations `SCIENTIFIC_MATCH`** (32/32 sides) and the supplementary
checker reports `OVERALL: PASS` with **4/4 configurations `SCIENTIFIC_MATCH`**
(8/8 sides). Exit code 0 means every configuration in scope is a
`SCIENTIFIC_MATCH`; exit 1 means at least one is not; exit 2 means an
environment or usage error. Add `--json` for a machine-readable report.

If you ran only an individual configuration (Step 6), the unselected
configurations are classified `NOT_RUN` — that is expected and correct. The
checker then exits 1 (because not every configuration in scope is a
`SCIENTIFIC_MATCH`); the run is successful when the summary shows your
selected configuration under `SCIENTIFIC_MATCH`, zero
`SCIENTIFIC_MISMATCH`/`INFRASTRUCTURE_FAILURE`/`PROVENANCE_MISMATCH`, and the
rest under `NOT_RUN`.

## Step 9 — Locate and interpret the evidence

Everything a reviewer needs is on disk under the output root:

```text
$RACELOOM_MATRIX_OUTPUT_ROOT/
├── status.tsv                     one row per execution attempt
├── <CONFIG_ID>/
│   ├── STATUS_COMPLETE            atomic success marker
│   ├── provenance.tsv             integrity record written before execution:
│   │                              input file hashes, image identity, repository
│   │                              identity, host environment
│   ├── console/                   console logs of both sides
│   └── artifacts/                 per-side RaceLoom run artifacts
│       ├── bad/                   final_stats.csv, run_*/harmful_traces/
│       └── control/               final_stats.csv, run_*/harmful_traces/
```

- `status.tsv` columns: `config_id, benchmark, depth, status, exit_code,
  utc_start, utc_end, evidence_dir, detail`.
- The scientific result of a side is in its console log's `Final Stats`
  block (`Generated traces:`, `Harmful races found:`, `Network model
  branches:`) and mirrored in `artifacts/<side>/final_stats.csv`.
- What the checker compares and how classifications work:
  [`docs/VALIDATION.md`](docs/VALIDATION.md).
- The verified reference results these should reproduce: [`docs/RESULTS.md`](docs/RESULTS.md).

## Troubleshooting

- **`docker: command not found`** — Docker is not installed or not on your
  `PATH`; see Step 2.
- **`Cannot connect to the Docker daemon`** / `docker daemon not accessible`
  — start Docker Desktop (macOS/Windows) or the Docker service (Linux), then
  retry.
- **`permission denied` while connecting to the daemon (Linux)** — add your
  user to the `docker` group (`sudo usermod -aG docker "$USER"`) and start a
  new shell.
- **Archive download fails or checksum mismatch** — the download needs
  network access to zenodo.org; retry `scripts/setup_raceloom_artifact.sh`.
  Never load or use an archive that failed verification.
- **`image ID mismatch`** — your local `raceloom:latest` is not the pinned
  reference image. Load the published archive with
  `scripts/setup_raceloom_artifact.sh`; only if you have independently
  established that a different image is correct, re-run with
  `RACELOOM_EXPECTED_IMAGE_ID=<id>` set.
- **macOS/Colima: Docker cannot see the benchmark files** — clone or move the
  repository under your home directory (not `/tmp`), which Colima shares by
  default, then retry.
- **A configuration is `BLOCKED` after an interruption** — the launchers
  never rerun incomplete evidence automatically. Inspect the configuration's
  directory; to retry deliberately, remove that configuration's evidence
  directory and rerun the launcher.
- **Slow or throttled laptop** — expected for the full matrix; see the
  hardware guidance above. The smoke test and individual configurations are
  the right laptop-sized checks.

## Licenses and attribution

This artifact uses a **multi-license structure**. The MIT license applies to
the *original RaceLoom-Bench material only* — it does **not** extend to
everything a reviewer downloads or executes:

- **Original RaceLoom-Bench material — MIT.** The benchmark models,
  properties, metadata, expected statistics, embeddings, scripts,
  documentation, and provenance records are licensed under the MIT License
  (`LICENSE`, which opens with a scope statement drawing exactly this
  boundary).
- **RaceLoom — Apache-2.0, obtained separately.** The execution engine inside
  the Docker image is *not* part of this repository and is not redistributed
  by it. It is obtained from the official RaceLoom artifact record (Zenodo
  DOI [10.5281/zenodo.16884345](https://doi.org/10.5281/zenodo.16884345)) and
  is licensed **Apache-2.0** (copyright Andrei-Ion Covaci). The image also
  bundles third-party components (KATch, OpenJDK, Graphviz, Python packages)
  under their own licenses.
- **Topology datasets — upstream terms.** Geant2012 is derived from the
  Internet Topology Zoo (**CC BY 4.0**; Knight et al. 2011 attribution
  required — redistribution is permitted with attribution). Atlanta,
  Nobel-EU, and Germany50 are derived from SNDlib networks, which are
  distributed under the **ZIB Academic License** (unmodified license text:
  `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt`). These upstream
  licenses govern their respective topology files — the assets in
  `topology_assets/` and the benchmark topology copies derived from them —
  as separately licensed components; the MIT license covers the rest of the
  repository and does not override them.

[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) is the authoritative
component-by-component licensing record: what the MIT license covers, what
each third-party component is licensed under, what redistribution is
permitted, and which attributions must be preserved. [`REUSE.toml`](REUSE.toml)
is the machine-readable file-to-license mapping.

**If you want to reuse or redistribute individual components:**

- *Original RaceLoom-Bench material* — use and redistribute freely under MIT,
  keeping the `LICENSE` notice.
- *Geant2012 derivative (`T3_geant2012.json` and its benchmark topology
  copy)* — redistribute under CC BY 4.0 with the attribution from
  `THIRD_PARTY_NOTICES.md` §6 / `topology_assets/README.md`, and indicate that
  it is an adapted abstraction of the upstream dataset.
- *SNDlib derivatives (`T1_atlanta.json`, `T2_nobel_eu.json`,
  `T4_germany50.json` and their benchmark topology copies)* — these carry the
  ZIB Academic License, not MIT; read the bundled license text before
  redistributing them. Alternatively, obtain the original networks directly
  from https://sndlib.put.poznan.pl/ (accepting the license there) and
  regenerate the assets with the committed generator — see
  `topology_assets/README.md`.
- *RaceLoom and its Docker image* — obtain from the official record and follow
  its license; this repository's MIT license does not cover them.

## Where to go next

| Document | Contents |
|---|---|
| [`README.md`](README.md) | Artifact overview, benchmark matrix, sources, license. |
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | Full installation details and hardware requirements. |
| [`docs/REPRODUCTION.md`](docs/REPRODUCTION.md) | Execution pipeline details, environment variables, resume behavior. |
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | Checker methodology, classifications, exit codes, test suites. |
| [`docs/RESULTS.md`](docs/RESULTS.md) | The verified reproduction results. |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | Licensing scope, third-party notices, and attribution requirements. |
| [`REUSE.toml`](REUSE.toml) | Machine-readable file-to-license mapping (REUSE 3.3). |
