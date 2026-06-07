# RaceLoom-Bench final 4×4 matrix

Format: `traces / bad harmful / control harmful`.

| Benchmark | T1 Atlanta | T2 Nobel-EU | T3 Geant2012 | T4 Germany50 |
|---|---:|---:|---:|---:|
| B1 waypoint / IDS-bypass | 156,100 / 62 / 0 | 49,980 / 38 / 0 | 82,688 / 44 / 0 | 129,276 / 50 / 0 |
| B2 wrong next-hop / route mapping | 96,309 / 74 / 0 | 37,856 / 25 / 0 | 64,800 / 29 / 0 | 104,040 / 33 / 0 |
| B3 slice isolation | 156,100 / 72 / 0 | 49,980 / 51 / 0 | 82,688 / 46 / 0 | 129,276 / 67 / 0 |
| B4 failover / stale path | 242,363 / 79 / 0 | 64,800 / 51 / 0 | 104,040 / 59 / 0 | 158,840 / 67 / 0 |

All 16 bad models expose harmful races.
All 16 control models expose zero harmful races.

T3 uses Topology Zoo Geant2012 instead of the earlier Cost266 attempt to avoid the suspicious repeated T2/T3 count issue.
