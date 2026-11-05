# Reproduction

This document describes how to execute the RaceLoom-Bench benchmarks with the canonical pipeline and how to reproduce the scientific results reported in `docs/RESULTS.md`. For the complete reviewer walkthrough (obtain, install, verify, smoke test, individual benchmarks, full reproduction, validation) start at `ARTIFACT.md`.

## Repository preparation

```bash
git clone https://github.com/sarmadiali98/RaceLoom-Bench.git
cd RaceLoom-Bench
```

Verify the working tree against the release checksum manifest:

```bash
sha256sum -c provenance/checksums.sha256        # Linux
shasum -a 256 -c provenance/checksums.sha256    # macOS
```

Install the RaceLoom runtime image first (`docs/INSTALLATION.md`), then configure the environment and verify it:

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
bash scripts/verify_environment.sh
```

Hardware requirements and expected execution times are documented in `docs/INSTALLATION.md` and `ARTIFACT.md`; the complete baseline-backed reproduction takes several hours even on the reference machine (approximately 6 logical CPUs, 30 GiB RAM).

## Environment variables

| Variable | Required | Meaning |
|---|---|---|
| `RACELOOM_IMAGE` | yes | Local RaceLoom Docker image, e.g. `raceloom:latest`. |
| `RACELOOM_MATRIX_OUTPUT_ROOT` | yes (launchers) | Existing directory **outside the repository** that receives all evidence. Relative paths resolve against the invocation directory. Must not be `/` or inside the repository (symlinks are resolved). |
| `RACELOOM_MATRIX_ONLY` | no | Run exactly one configuration ID instead of the full set (see *Single-configuration execution*). |
| `RACELOOM_WORKDIR` | no | Image directory containing `main.py` (default `/raceloom`). |
| `DOCKER_PLATFORM` | no | Forwarded as `docker run --platform` when set (e.g. `linux/amd64` on Apple Silicon). |
| `RACELOOM_OUTPUT_DIR` | no | Set by the launchers per configuration; binds a host directory over the container's `output` directory so RaceLoom `run_*` artifacts persist. Manual users may set it with the pair runner; it must exist and lie outside the repository. |

The canonical pipeline runs `python3 main.py -d <depth> -s <strategy>` inside the container with the model and property files mounted read-only; no interpreter override is needed or used.

## Execution levels

Keep the four levels apart:

| Level | Command | Scope |
|---|---|---|
| Smoke test | `bash scripts/docker_smoke_test.sh` | One miniature pair through the canonical pipeline; verifies the installation in ~1 minute. Not part of the scientific reproduction. |
| Individual configuration | `RACELOOM_MATRIX_ONLY=<ID> bash scripts/run_final_matrix.sh` (or the supplementary launcher) | Exactly one baseline-backed configuration, full provenance. |
| Principal reproduction | `bash scripts/run_final_matrix.sh` | All 16 baseline-backed principal configurations. |
| Supplementary reproduction | `bash scripts/run_supplementary_matrix.sh` | All 4 baseline-backed supplementary configurations. |

The smoke benchmark (`benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta`) has no historical baseline; it is an installation check and is never counted among the scientific reproductions.

## Principal matrix execution

The principal matrix is the 16-configuration B1--B4 × {K8, K12, K14, K16} set (`benchmarks/final/`), faulty side first, depth 5 for K8 configurations and depth 4 for K12/K14/K16, strategy BFS:

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_MATRIX_OUTPUT_ROOT=/path/to/evidence-root
bash scripts/run_final_matrix.sh
```

The launcher executes the 16 configurations sequentially. Reference wall-clock time for the full principal matrix was ~6.8 h on the validation server (2026-11-04, 09:47–16:34 UTC); individual configurations take between ~5 min (B2_K8_T1_atlanta) and ~1 h (B4_K16_T4_germany50).

## Supplementary execution

The supplementary group is the 4-configuration synthetic S1--S4 set (`benchmarks/synthetic/final/`):

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_MATRIX_OUTPUT_ROOT=/path/to/evidence-root
bash scripts/run_supplementary_matrix.sh
```

Reference wall-clock time for the full supplementary group was ~1.3 h (2026-11-04, 17:06–18:23 UTC).

## Single-configuration execution

Set `RACELOOM_MATRIX_ONLY` to exactly one configuration ID:

```bash
RACELOOM_MATRIX_ONLY=B2_K14_T3_geant2012 bash scripts/run_final_matrix.sh
RACELOOM_MATRIX_ONLY=S1_multidomain_wrong_destination bash scripts/run_supplementary_matrix.sh
```

The value must match one configuration ID exactly; empty, unknown, comma-separated, glob-like, or path-like values abort before anything runs. Exit 0 in selection mode means the **selected** configuration completed operationally; it does not mean the full set was reproduced (the checker classifies unselected configurations as `NOT_RUN`, and therefore exits 1 after a selection-only run; a selection-only validation is successful when the selected configuration is `SCIENTIFIC_MATCH` with zero mismatch/failure classifications and the rest are `NOT_RUN`). A later full-set invocation with the same output root skips the completed configuration and continues with the rest.

Alternatively, run one pair directly through the pair runner (no launcher bookkeeping, no provenance record):

```bash
bash scripts/run_one_pair.sh benchmarks/final/b2_route_mapping_forced_distinct/K14/T3_geant2012 4 /path/to/console-dir
```

## Resume behavior

Both launchers are resumable. Reusing the same `RACELOOM_MATRIX_OUTPUT_ROOT`:

- Configurations with valid completion evidence (`STATUS_COMPLETE` marker + consistent `status.tsv` record) are **skipped without executing** and recorded as `SKIPPED_ALREADY_COMPLETE`.
- Incomplete or failed configurations are reported `BLOCKED` and **never rerun automatically**; remove that configuration's evidence directory to retry it deliberately.
- A lock directory (`.matrix_lock` / `.supplementary_lock`) prevents concurrent launchers on the same root.
- `STATUS_IN_PROGRESS` markers survive crashes and mark interrupted configurations.

## Output directory structure

For each configuration `<ID>` the launcher creates:

```text
<RACELOOM_MATRIX_OUTPUT_ROOT>/
├── status.tsv                     one row per execution attempt (TSV)
├── <ID>/
│   ├── STATUS_COMPLETE            atomic success marker (exit 0 + minimum evidence)
│   ├── provenance.tsv             key=value integrity record written before execution
│   ├── console/                   console logs of both sides
│   │   ├── <bench>_<side>_depth<N>.log
│   ├── artifacts/                 per-side RaceLoom run artifacts
│   │   ├── bad/
│   │   │   ├── final_stats.csv
│   │   │   └── run_<timestamp>/{harmful_traces/, harmful_traces_raw/}
│   │   └── control/
│   │       ├── final_stats.csv
│   │       └── run_<timestamp>/{harmful_traces/, harmful_traces_raw/}
```

`status.tsv` columns: `config_id, benchmark, depth, status, exit_code, utc_start, utc_end, evidence_dir, detail`. `provenance.tsv` records benchmark identity, SHA-256 hashes of all four executed input files, the requested and resolved Docker image identity, the repository branch/HEAD/working-tree fingerprint, the executing script hashes, and host environment identity. In working trees without a `.git` directory (e.g. release archives extracted from a zip), the repository identity is recorded as `not_a_git_repository`/`not_available` and the working-tree fingerprint is computed directly over the extracted files; the independent checkers treat these values as informational and never classify on them.

## Reproducibility considerations

- **Deterministic scientific metrics.** Generated-trace counts, harmful-race counts, and branch signatures are deterministic for a given model, property, depth, and strategy. These are the quantities the independent checkers compare; all 20 baseline-backed configurations matched (see `docs/RESULTS.md`).
- **Timing is a measurement, not a criterion.** Wall-clock fields (trace generation, Maude, KATch, analyzer, total) vary with host, load, and cache state. The checkers record them as measurements and never classify on them.
- **Cache counters.** Trace-generation and KATch cache hit/miss counters are compared against the historical logs by the checkers and matched in the reference reproduction.
- **Runtime identity.** Record and reuse the same RaceLoom image; the provenance records capture the resolved image ID of every execution.
- **Platform.** Execute natively on Linux amd64 for representative runtimes. Emulated execution on Apple Silicon is suitable for smoke testing; scientific counts are unaffected by emulation, but timings are not comparable.
- **Do not rerun to "fix" results.** If a configuration fails, inspect the evidence and environment; the checkers are read-only and the historical expectations are immutable.
