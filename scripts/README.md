# Scripts

This directory contains the scripts for running, checking, and reproducing the benchmark artifact.

## Canonical execution pipeline

The canonical Docker execution path is:

```text
docker_smoke_test.sh / run_final_matrix.sh / run_supplementary_matrix.sh   (entry points)
        └── run_one_pair.sh                              (bad/control pair runner)
                └── run_raceloom_progress.sh             (single Docker-backed RaceLoom run)
```

Each launcher requires `RACELOOM_MATRIX_OUTPUT_ROOT` (an existing directory outside this repository) and `RACELOOM_IMAGE` (a local RaceLoom Docker image). Per configuration it records console logs, per-side RaceLoom artifacts (`final_stats.csv`, harmful traces), a `provenance.tsv` integrity record, status markers, and a root `status.tsv`. Reusing the same output root resumes: completed configurations are skipped, never rerun.

The wrapper `run_raceloom_progress.sh` mounts the model and property files read-only into the RaceLoom container and runs `python3 main.py -d <depth> -s <strategy>`; it never modifies benchmark inputs.

## Script inventory

| Script | Purpose |
|---|---|
| `setup_raceloom_artifact.sh` | Downloads the external RaceLoom Docker artifact from Zenodo, verifies the archive SHA-256, loads it, and verifies the loaded image ID against the pinned reference image. |
| `verify_environment.sh` | Reviewer preflight: per-check PASS/FAIL for Docker, the RaceLoom image (with pinned-ID check), Python 3, the SHA-256 tool, and the release checksum manifest. |
| `docker_smoke_test.sh` | Runs the default fast smoke test (B2 smoke pair, depth 4) through the canonical pair runner, persists both sides' artifacts outside the repository, and checks the exact expected scientific outcome. |
| `docker_run_pair.sh` | Legacy/manual runner for one bad/control benchmark pair inside a RaceLoom Docker image (console logs only; not used by the smoke test or the canonical pipeline). |
| `check_pair_result.py` | Checks generated smoke logs against expected traces, harmful-race counts, and (optionally) the branch signature. |
| `run_raceloom_progress.sh` | Canonical Docker-backed wrapper for a single RaceLoom run (model + property, depth, strategy). |
| `run_one_pair.sh` | Canonical pair runner: faulty side first, then control side, console logs via `tee`. |
| `run_final_matrix.sh` | Canonical sequential, resumable launcher for the 16-configuration principal B1--B4 matrix (supports `RACELOOM_MATRIX_ONLY` single-configuration selection). |
| `run_supplementary_matrix.sh` | Canonical sequential, resumable launcher for the 4-configuration supplementary S1--S4 group (supports `RACELOOM_MATRIX_ONLY` single-configuration selection). |
| `check_final_matrix.py` | Independent, read-only scientific checker for the principal matrix (16 configurations). |
| `test_check_final_matrix.py` | Test suite for the principal checker (69 tests). |
| `check_supplementary_matrix.py` | Independent, read-only scientific checker for the supplementary S1--S4 group (4 configurations). |
| `test_check_supplementary_matrix.py` | Test suite for the supplementary checker (24 tests). |
| `test_matrix_selection.sh` | Mocked test suite for `RACELOOM_MATRIX_ONLY` selection on both launchers (19 tests; no real Docker). |
| `test_reviewer_scripts.sh` | Mocked test suite for `verify_environment.sh`, `docker_smoke_test.sh`, and the pair checker (18 tests; no real Docker). |
| `generate_checksum_manifest.sh` | Regenerates `provenance/checksums.sha256` over the documented release-critical file scope. |
| `extract_paper_numbers_from_logs.py` | Parses sanitized historical validation logs and checks reproduced numbers against committed summary TSV files. |
| `summarize_logs.py` | Helper for summarizing RaceLoom logs. |

The checkers and their test suites use the Python 3 standard library only and never execute RaceLoom or Docker. See `docs/VALIDATION.md` for checker usage, exit codes, and classification definitions.

## Environment variables

| Variable | Used by | Meaning |
|---|---|---|
| `RACELOOM_IMAGE` | all Docker paths | Local RaceLoom Docker image (required), e.g. `raceloom:latest`. |
| `RACELOOM_WORKDIR` | `run_raceloom_progress.sh`, `docker_run_pair.sh` | Image directory containing `main.py` (default `/raceloom`). |
| `DOCKER_PLATFORM` | all Docker paths | Forwarded as `docker run --platform` when set (e.g. `linux/amd64` on Apple Silicon). |
| `RACELOOM_OUTPUT_DIR` | `run_one_pair.sh`, `run_raceloom_progress.sh` | Optional host directory for persistent RaceLoom `run_*` artifacts; must exist and lie outside the repository. |
| `RACELOOM_MATRIX_OUTPUT_ROOT` | `run_final_matrix.sh`, `run_supplementary_matrix.sh` | Required evidence root directory (outside the repository). |
| `RACELOOM_MATRIX_ONLY` | both launchers | Optional: run exactly one configuration ID instead of the full set. |
| `RACELOOM_SMOKE_OUTPUT_ROOT` | `docker_smoke_test.sh` | Optional smoke output root (default `$HOME/raceloom-bench-smoke`; also settable via `--output-root`). |
| `RACELOOM_EXPECTED_IMAGE_ID` | `setup_raceloom_artifact.sh`, `verify_environment.sh` | Overrides the pinned image identity; use only after independently establishing that a different image is correct. |
| `RACELOOM_CMD` | `docker_run_pair.sh` only | Interpreter command inside the container (default `python main.py`). Not used by the canonical pipeline, which runs `python3 main.py`. |
| `RACELOOM_ARCHIVE` | `setup_raceloom_artifact.sh` | Optional download filename (default `raceloom.tar.gz`; an explicitly provided path is never deleted or overwritten). |
