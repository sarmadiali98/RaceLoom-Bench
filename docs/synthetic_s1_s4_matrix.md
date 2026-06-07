# Synthetic S1-S4 benchmark matrix

These benchmarks are the curated S1--S4 synthetic benchmark set.

Format: `generated traces / bad harmful / control harmful`.

| ID | Scenario | Depth / strategy | Branch structure | Result |
|---|---|---:|---|---:|
| S1 | Multidomain wrong destination | 5 / bfs | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 / 396 / 0 |
| S2 | Hierarchical extended wrong destination | 4 / bfs | `C1:7;C2:7;CM:2;BSw:15` | 38,478 / 31 / 0 |
| S3 | Multi-slice shared-core isolation | 5 / bfs | `C1:6;C2:6;BSw:13` | 363,024 / 104 / 0 |
| S4 | Multi-region stale reroute | 5 / bfs | `C1:5;C2:6;CM:2;BSw:12` | 150,533 / 18 / 0 |

All four faulty synthetic models expose harmful races.
All four control synthetic models expose zero harmful races.
