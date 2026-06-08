# S3 multi-slice shared-core isolation

This directory contains the S3 synthetic benchmark pair.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `metadata.json` | Benchmark metadata. |
| `expected_stats.md` | Expected result summary. |
| `trace_validation.md` | Trace-validation notes. |
| `run_s3.sh` | Local helper script. |

Expected result at depth 5 with BFS: 363,024 traces, 104 harmful races in the faulty model, and 0 harmful races in the control model.
