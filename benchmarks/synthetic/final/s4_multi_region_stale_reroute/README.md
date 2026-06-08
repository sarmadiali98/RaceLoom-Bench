# S4 multi-region stale reroute

This directory contains the S4 synthetic benchmark pair.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `metadata.json` | Benchmark metadata. |
| `expected_stats.md` | Expected result summary. |
| `trace_validation.md` | Trace-validation notes. |
| `run_s4.sh` | Local helper script. |

Expected result at depth 5 with BFS: 150,533 traces, 18 harmful races in the faulty model, and 0 harmful races in the control model.
