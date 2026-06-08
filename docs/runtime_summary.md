# Runtime summary

This file summarizes the recorded runtimes for the benchmark sets in this repository.

## Full B1--B4 matrix runtime summary

These runs were performed on the validation server described above. Times are reported as faulty/control wall-clock execution times when available in the benchmark metadata.

| Benchmark | Topology | Depth | Generated traces | Harmful races faulty/control | Runtime faulty/control |
|---|---|---:|---:|---:|---:|
| B1_waypoint_order | T1_atlanta | 5 | 156,100 | 62/0 | n/a / n/a |
| B1_waypoint_order | T2_nobel_eu | 4 | 49,980 | 38/0 | n/a / n/a |
| B1_waypoint_order | T3_geant2012 | 4 | 82,688 | 44/0 | n/a / n/a |
| B1_waypoint_order | T4_germany50 | 4 | 129,276 | 50/0 | n/a / n/a |
| B2_route_mapping | T1_atlanta | 5 | 96,309 | 74/0 | n/a / n/a |
| B2_route_mapping | T2_nobel_eu | 4 | 37,856 | 25/0 | n/a / n/a |
| B2_route_mapping | T3_geant2012 | 4 | 64,800 | 29/0 | n/a / n/a |
| B2_route_mapping | T4_germany50 | 4 | 104,040 | 33/0 | n/a / n/a |
| B3_slice_isolation | T1_atlanta | 5 | 156,100 | 72/0 | n/a / n/a |
| B3_slice_isolation | T2_nobel_eu | 4 | 49,980 | 51/0 | n/a / n/a |
| B3_slice_isolation | T3_geant2012 | 4 | 82,688 | 46/0 | n/a / n/a |
| B3_slice_isolation | T4_germany50 | 4 | 129,276 | 67/0 | n/a / n/a |
| B4_failover_cleanup | T1_atlanta | 5 | 242,363 | 79/0 | n/a / n/a |
| B4_failover_cleanup | T2_nobel_eu | 4 | 64,800 | 51/0 | n/a / n/a |
| B4_failover_cleanup | T3_geant2012 | 4 | 104,040 | 59/0 | n/a / n/a |
| B4_failover_cleanup | T4_germany50 | 4 | 158,840 | 67/0 | n/a / n/a |

Some B1--B4 runtime entries were not available in the committed metadata. The result counts are still recorded in `docs/final_4x4_matrix.tsv`.

## Synthetic S1--S4 runtime summary

These runs were performed on the same validation server.

| ID | Scenario | Depth | Generated traces | Harmful races faulty/control | Runtime faulty/control |
|---|---|---:|---:|---:|---:|
| S1 | Multidomain wrong destination | 5 | 363,024 | 396/0 | 23.80 min / 10.71 min |
| S2 | Hierarchical extended wrong destination | 4 | 38,478 | 31/0 | 17.49 min / 17.65 min |
| S3 | Multi-slice shared-core isolation | 5 | 363,024 | 104/0 | 21.46 min / 14.45 min |
| S4 | Multi-region stale reroute | 5 | 150,533 | 18/0 | 15.92 min / 16.09 min |

Approximate total S1--S4 synthetic runtime: **137.58 min**.
