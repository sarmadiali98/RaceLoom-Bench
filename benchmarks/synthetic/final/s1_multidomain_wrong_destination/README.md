# S1 multidomain wrong destination

This directory contains the S1 synthetic benchmark pair.

S1 models a multidomain wrong-destination scenario. The benchmark has paired faulty and control RaceLoom models. The faulty model exposes the intended harmful race, while the control model exposes zero harmful races under the same depth and trace-generation strategy.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `metadata.json` | Benchmark metadata. |
| `expected_stats.md` | Expected result summary. |
| `trace_validation.md` | Trace-validation notes. |
| `run_s1.sh` | Local helper script. |

Expected result at depth 5 with BFS:

| Model | Branch structure | Generated traces | Harmful races | Total execution time |
|---|---|---:|---:|---:|
| faulty | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 | 396 | 1427.731890576193s |
| control | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 | 0 | 642.8721467598807s |
