# Validation

This document describes the two independent, read-only scientific checkers that verify RaceLoom-Bench reproduction evidence against the historical expectations, and how to interpret their results.

## The two independent checkers

| Checker | Scope | Expectations |
|---|---|---|
| `scripts/check_final_matrix.py` | Principal matrix: 16 configurations (B1--B4 × K8/K12/K14/K16), 32 sides | `docs/final_4x4_matrix.tsv` + `docs/validation_logs/main/` (32 historical logs) |
| `scripts/check_supplementary_matrix.py` | Supplementary group: 4 configurations (S1--S4), 8 sides | `docs/synthetic_s1_s4_matrix.tsv` + `docs/validation_logs/synthetic/` (8 historical logs) |

Both checkers:

- never execute RaceLoom or Docker,
- never modify any input or evidence file (read-only),
- use the Python 3 standard library only,
- verify the evidence layout, completion markers, provenance integrity, console-log/final-stats agreement, and the scientific metrics.

The supplementary checker is deliberately separate (different expectation schema, different historical log names) but reuses the principal checker's tested parsing and evaluation components.

## Command-line arguments

```bash
python3 scripts/check_final_matrix.py --matrix-root /path/to/evidence-root
python3 scripts/check_final_matrix.py --matrix-root ROOT --json
python3 scripts/check_final_matrix.py --matrix-root ROOT --output report.json

python3 scripts/check_supplementary_matrix.py --matrix-root /path/to/evidence-root
python3 scripts/check_supplementary_matrix.py --matrix-root ROOT --json
python3 scripts/check_supplementary_matrix.py --matrix-root ROOT --output report.json
```

| Argument | Meaning |
|---|---|
| `--matrix-root ROOT` | Evidence root produced by `scripts/run_final_matrix.sh` or `scripts/run_supplementary_matrix.sh` (required). |
| `--json` | Print the full JSON report to stdout in addition to the human-readable summary. |
| `--output FILE` | Write the full JSON report to `FILE`. |

The checkers locate the repository (expectation sources) relative to their own script location, so they must be invoked from the repository checkout that contains `docs/final_4x4_matrix.tsv` (respectively `docs/synthetic_s1_s4_matrix.tsv`) and the sanitized historical logs.

## Expected input evidence

For each configuration `<ID>`, under `--matrix-root`:

```text
status.tsv                       root-level execution ledger
<ID>/STATUS_COMPLETE             atomic success marker
<ID>/provenance.tsv              key=value integrity record
<ID>/console/<bench>_<side>_depth<N>.log   console logs (both sides)
<ID>/artifacts/<side>/final_stats.csv      per-side final statistics
<ID>/artifacts/<side>/run_*/harmful_traces{,_raw}/  preserved harmful traces
```

## Scientific comparison methodology

For each side (faulty `bad/`, control `control/`) the checkers extract the scientific fields from the console log's `Final Stats` block and cross-check them against the side's `final_stats.csv`; the two sources must agree. The agreed values are then compared with the expectations:

| Field | Expectation source | Comparison |
|---|---|---|
| Generated traces | Matrix TSV (`traces`) | Exact integer equality |
| Harmful races | Matrix TSV (`bad_harmful` / `control_harmful`) | Exact integer equality |
| Branch signature | Matrix TSV (`branches`) | Order-independent branch-name/count mapping (e.g. `CBg:14;CRoute:1;BSw:16` equals `CRoute:1;CBg:14;BSw:16`); malformed signatures or duplicate branch names can never match |
| Depth | Matrix TSV (`depth`) | Exact equality |
| Strategy | Hard-coded `bfs` | Exact equality |
| Cache counters (`gen_cache_hits`, `gen_cache_misses`, `katch_cache_hits`, `katch_cache_misses`) | Historical validation log | Exact integer equality |

Timing fields (trace generation, Maude, KATch, analyzer, total execution time) are recorded in the report as measurements only and **never** produce scientific mismatches.

Additionally, the checkers verify evidence integrity:

- **Provenance record**: schema identity, configuration identity, benchmark path, depth, strategy, execution order, and the SHA-256 hashes of all four executed input files recomputed against the current repository files (`bad/model.json`, `bad/properties.json`, `control/model.json`, `control/properties.json`). Any disagreement is a `PROVENANCE_MISMATCH`.
- **Harmful-trace evidence**: a side reporting harmful races > 0 must have preserved harmful trace files under `artifacts/<side>/run_*/harmful_traces`.
- **Completion evidence**: `STATUS_COMPLETE` marker, `status.tsv` records, and exit codes must be mutually consistent.

## Classification definitions

Each configuration receives exactly one classification:

| Classification | Meaning |
|---|---|
| `SCIENTIFIC_MATCH` | All scientific fields (traces, harmful races, branch signature, depth, strategy, cache counters) match the expectations, all evidence integrity checks pass. |
| `SCIENTIFIC_MISMATCH` | Evidence is complete and consistent, but at least one scientific field differs from the expectations. |
| `INFRASTRUCTURE_FAILURE` | The execution infrastructure failed (nonzero exit recorded with operational-success claims, launcher-reported failure). |
| `INCOMPLETE_EVIDENCE` | Evidence is missing, empty, inconsistent, or interrupted (missing logs/stats, marker conflicts, `STATUS_IN_PROGRESS`, missing harmful traces). |
| `NOT_RUN` | No execution evidence exists for the configuration (e.g. after a `RACELOOM_MATRIX_ONLY` selection run). |
| `PROVENANCE_MISMATCH` | The provenance record disagrees with the repository or the evidence layout (input-hash mismatch, wrong schema/config/path). |

The classifications are severity-ordered; the most severe finding determines the configuration's classification.

## Test-suite execution

Both checkers ship with self-contained test suites (standard library only, no RaceLoom or Docker required):

```bash
python3 scripts/test_check_final_matrix.py          # 69 tests
python3 scripts/test_check_supplementary_matrix.py  # 24 tests
```

Expected output ends with the test count and `OK`. The suites were verified on both development machines (macOS and Ubuntu) during release preparation.

## Exit-code interpretation

| Exit code | Meaning |
|---|---|
| `0` | All configurations in scope are `SCIENTIFIC_MATCH`. |
| `1` | Validation unsuccessful: at least one configuration has a classification other than `SCIENTIFIC_MATCH`. |
| `2` | Environment or usage error (missing expectation sources, malformed matrix TSV, unreadable matrix root, ...). No scientific verdict is implied. |

## Reference validation results

On the release validation evidence (2026-11-04, Linux amd64 server, Docker image `sha256:fe13627b…`):

- Principal checker: 16/16 configurations `SCIENTIFIC_MATCH`, 32/32 sides with valid evidence — `OVERALL: PASS`.
- Supplementary checker: 4/4 configurations `SCIENTIFIC_MATCH`, 8/8 sides with valid evidence — `OVERALL: PASS`.

The checker reports are preserved in the release evidence archive; see `docs/RESULTS.md`.
