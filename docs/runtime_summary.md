# Runtime summary

This file reports exact recorded runtimes extracted from the validation logs.

## Validation server

- OS: Ubuntu 24.04.3 LTS
- Kernel: Linux gpu1 6.8.0-87-generic #88-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 09:28:41 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
- CPU model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz
- CPUs reported by `lscpu`: 64
- CPUs reported by `nproc --all`: 128
- CPUs available to the process from `nproc`: 64
- Memory: 135025090560 bytes = 125.751915 GiB = 135.025091 GB
- Python: 3.13.5
- Java: OpenJDK 1.8.0_492
- RaceLoom `main.py` SHA-256: `c77059168460593a2980f23398b73cc3dd68e646466fb380371e83bce515f120`

## Main B1--B4 matrix

| ID | Family | Case | Side | Depth | Branches | Traces | Harmful races | Total execution time |
|---|---|---|---|---:|---|---:|---:|---:|
| B1 | waypoint / IDS-bypass | K8/T1_atlanta | bad | 5 | `CBg:8;CIngress:1;CWaypoint:1;BSw:11` | 156,100 | 62 | 563.535412s |
| B1 | waypoint / IDS-bypass | K8/T1_atlanta | control | 5 | `CBg:8;CIngress:1;CWaypoint:1;BSw:11` | 156,100 | 0 | 572.474434s |
| B1 | waypoint / IDS-bypass | K12/T2_nobel_eu | bad | 4 | `CBg:12;CIngress:1;CWaypoint:1;BSw:15` | 49,980 | 38 | 833.762204s |
| B1 | waypoint / IDS-bypass | K12/T2_nobel_eu | control | 4 | `CBg:12;CIngress:1;CWaypoint:1;BSw:15` | 49,980 | 0 | 837.102106s |
| B1 | waypoint / IDS-bypass | K14/T3_geant2012 | bad | 4 | `CIngress:1;CWaypoint:1;CBg:14;BSw:17` | 82,688 | 44 | 1432.474120s |
| B1 | waypoint / IDS-bypass | K14/T3_geant2012 | control | 4 | `CIngress:1;CWaypoint:1;CBg:14;BSw:17` | 82,688 | 0 | 889.606072s |
| B1 | waypoint / IDS-bypass | K16/T4_germany50 | bad | 4 | `CBg:16;CIngress:1;CWaypoint:1;BSw:19` | 129,276 | 50 | 1972.720083s |
| B1 | waypoint / IDS-bypass | K16/T4_germany50 | control | 4 | `CBg:16;CIngress:1;CWaypoint:1;BSw:19` | 129,276 | 0 | 2369.630452s |
| B2 | wrong next-hop / route mapping | K8/T1_atlanta | bad | 5 | `CBg:8;CRoute:1;BSw:10` | 96,309 | 74 | 286.921927s |
| B2 | wrong next-hop / route mapping | K8/T1_atlanta | control | 5 | `CBg:8;CRoute:1;BSw:10` | 96,309 | 0 | 301.237840s |
| B2 | wrong next-hop / route mapping | K12/T2_nobel_eu | bad | 4 | `CBg:12;CRoute:1;BSw:14` | 37,856 | 25 | 535.127057s |
| B2 | wrong next-hop / route mapping | K12/T2_nobel_eu | control | 4 | `CBg:12;CRoute:1;BSw:14` | 37,856 | 0 | 548.866781s |
| B2 | wrong next-hop / route mapping | K14/T3_geant2012 | bad | 4 | `CRoute:1;CBg:14;BSw:16` | 64,800 | 29 | 1208.228198s |
| B2 | wrong next-hop / route mapping | K14/T3_geant2012 | control | 4 | `CRoute:1;CBg:14;BSw:16` | 64,800 | 0 | 953.507350s |
| B2 | wrong next-hop / route mapping | K16/T4_germany50 | bad | 4 | `CBg:16;CRoute:1;BSw:18` | 104,040 | 33 | 1254.254325s |
| B2 | wrong next-hop / route mapping | K16/T4_germany50 | control | 4 | `CBg:16;CRoute:1;BSw:18` | 104,040 | 0 | 1327.450590s |
| B3 | slice isolation | K8/T1_atlanta | bad | 5 | `CBg:8;CSliceA:1;CSliceB:1;BSw:11` | 156,100 | 72 | 488.524798s |
| B3 | slice isolation | K8/T1_atlanta | control | 5 | `CBg:8;CSliceA:1;CSliceB:1;BSw:11` | 156,100 | 0 | 491.611782s |
| B3 | slice isolation | K12/T2_nobel_eu | bad | 4 | `CBg:12;CSliceA:1;CSliceB:1;BSw:15` | 49,980 | 51 | 660.107199s |
| B3 | slice isolation | K12/T2_nobel_eu | control | 4 | `CBg:12;CSliceA:1;CSliceB:1;BSw:15` | 49,980 | 0 | 667.077585s |
| B3 | slice isolation | K14/T3_geant2012 | bad | 4 | `CBg:14;CSliceA:1;CSliceB:1;BSw:17` | 82,688 | 46 | 1217.651288s |
| B3 | slice isolation | K14/T3_geant2012 | control | 4 | `CBg:14;CSliceA:1;CSliceB:1;BSw:17` | 82,688 | 0 | 1228.407852s |
| B3 | slice isolation | K16/T4_germany50 | bad | 4 | `CBg:16;CSliceA:1;CSliceB:1;BSw:19` | 129,276 | 67 | 1638.457789s |
| B3 | slice isolation | K16/T4_germany50 | control | 4 | `CBg:16;CSliceA:1;CSliceB:1;BSw:19` | 129,276 | 0 | 1654.885645s |
| B4 | failover / stale path | K8/T1_atlanta | bad | 5 | `CBg:8;CDetect:1;CFailover:1;CCleanup:1;BSw:12` | 242,363 | 79 | 916.026407s |
| B4 | failover / stale path | K8/T1_atlanta | control | 5 | `CBg:8;CDetect:1;CFailover:1;CCleanup:1;BSw:12` | 242,363 | 0 | 355.674991s |
| B4 | failover / stale path | K12/T2_nobel_eu | bad | 4 | `CBg:12;CDetect:1;CFailover:1;CCleanup:1;BSw:16` | 64,800 | 51 | 1179.817474s |
| B4 | failover / stale path | K12/T2_nobel_eu | control | 4 | `CBg:12;CDetect:1;CFailover:1;CCleanup:1;BSw:16` | 64,800 | 0 | 1158.172184s |
| B4 | failover / stale path | K14/T3_geant2012 | bad | 4 | `CBg:14;CDetect:1;CFailover:1;CCleanup:1;BSw:18` | 104,040 | 59 | 1821.278689s |
| B4 | failover / stale path | K14/T3_geant2012 | control | 4 | `CBg:14;CDetect:1;CFailover:1;CCleanup:1;BSw:18` | 104,040 | 0 | 1879.773365s |
| B4 | failover / stale path | K16/T4_germany50 | bad | 4 | `CBg:16;CDetect:1;CFailover:1;CCleanup:1;BSw:20` | 158,840 | 67 | 2689.636385s |
| B4 | failover / stale path | K16/T4_germany50 | control | 4 | `CBg:16;CDetect:1;CFailover:1;CCleanup:1;BSw:20` | 158,840 | 0 | 2704.822722s |

Total recorded B1--B4 matrix runtime: **36638.825103s** = **610.647 min**.

## Synthetic S1--S4 benchmarks

| ID | Scenario | Side | Depth | Branches | Traces | Harmful races | Total execution time |
|---|---|---|---:|---|---:|---:|---:|
| S1 | Multidomain wrong destination | bad | 5 | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 | 396 | 1427.731891s |
| S1 | Multidomain wrong destination | control | 5 | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 | 0 | 642.872147s |
| S2 | Hierarchical extended wrong destination | bad | 4 | `C1:7;C2:7;CM:2;BSw:15` | 38,478 | 31 | 1049.240204s |
| S2 | Hierarchical extended wrong destination | control | 4 | `C1:7;C2:7;CM:2;BSw:15` | 38,478 | 0 | 1059.224928s |
| S3 | Multi-slice shared-core isolation | bad | 5 | `C1:6;C2:6;BSw:13` | 363,024 | 104 | 1287.352348s |
| S3 | Multi-slice shared-core isolation | control | 5 | `C1:6;C2:6;BSw:13` | 363,024 | 0 | 867.276945s |
| S4 | Multi-region stale reroute | bad | 5 | `C1:5;C2:6;CM:2;BSw:12` | 150,533 | 18 | 955.192787s |
| S4 | Multi-region stale reroute | control | 5 | `C1:5;C2:6;CM:2;BSw:12` | 150,533 | 0 | 965.633272s |

Total recorded S1--S4 synthetic runtime: **8254.524522s** = **137.575 min**.
