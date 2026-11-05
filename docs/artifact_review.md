# Artifact review guide

**Start at [`ARTIFACT.md`](../ARTIFACT.md)** — the reviewer-facing quick start covering installation, environment verification, the smoke test, individual benchmark execution, the complete reproduction, and independent validation. It assumes no prior knowledge of this project.

This repository contains benchmark inputs and helper scripts for RaceLoom. It does not include RaceLoom itself. RaceLoom should be obtained from the RaceLoom artifact record on Zenodo:

https://doi.org/10.5281/zenodo.16884345

Detailed guides: `docs/INSTALLATION.md` (setup and hardware requirements), `docs/REPRODUCTION.md` (execution), `docs/VALIDATION.md` (independent checkers), and `docs/RESULTS.md` (verified results).

## Reviewer smoke test

The default smoke test runs a small B2 route-mapping benchmark pair through the canonical pipeline:

    bash scripts/docker_smoke_test.sh

Expected result:

| Model | Generated traces | Harmful races | Branch signature |
|---|---:|---:|---|
| B2 smoke faulty | 8 | 1 | `CRoute:1;BSw:2` |
| B2 smoke control | 8 | 0 | `CRoute:1;BSw:2` |

A successful run ends with:

    SMOKE TEST: PASS

Smoke evidence is persisted outside the repository under `~/raceloom-bench-smoke/smoke_<timestamp>/` (override with `--output-root DIR`).

## Independent validation

After execution, the independent read-only checkers compare the new evidence against the historical expectations:

    python3 scripts/check_final_matrix.py --matrix-root "$RACELOOM_MATRIX_OUTPUT_ROOT"
    python3 scripts/check_supplementary_matrix.py --matrix-root "$RACELOOM_MATRIX_OUTPUT_ROOT"

Exit code 0 means every configuration is classified `SCIENTIFIC_MATCH`. See `docs/VALIDATION.md` for arguments, classifications, and exit codes.

## Verification status

The principal matrix (16/16 configurations) and the supplementary group (4/4 configurations) were reproduced on the project's Linux amd64 validation server (Docker, image `sha256:fe13627b…`) on 2026-11-04 and classified `SCIENTIFIC_MATCH` by both independent checkers. See `docs/RESULTS.md`.

## Full benchmark reruns

The full B1--B4 and S1--S4 benchmark suites can take substantially longer than the smoke test. They are intended for a native Ubuntu/Linux amd64 machine comparable to the reference reproduction host (approximately 6 logical CPUs and 30 GiB RAM); see `docs/INSTALLATION.md` for the hardware guidance and laptop warning.

Reference summaries are available in:

- `docs/final_4x4_matrix.md`
- `docs/final_4x4_matrix.tsv`
- `docs/synthetic_s1_s4_matrix.md`
- `docs/synthetic_s1_s4_matrix.tsv`
- `docs/RESULTS.md`
