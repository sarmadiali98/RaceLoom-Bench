# Results

This document reports the verified scientific results of the RaceLoom-Bench reproduction. All numbers are grounded in committed expectations and preserved evidence; the evidence archive contains the raw artifacts behind every figure.

## Verification summary

| Set | Configurations | Sides | Checker | Result |
|---|---:|---:|---|---|
| Principal matrix (B1--B4 × K8/K12/K14/K16) | 16 | 32 | `scripts/check_final_matrix.py` | 16/16 `SCIENTIFIC_MATCH` |
| Supplementary group (S1--S4) | 4 | 8 | `scripts/check_supplementary_matrix.py` | 4/4 `SCIENTIFIC_MATCH` |

- **20 of 20 baseline-backed configurations reproduced** (40 single-model executions: 32 principal + 8 supplementary).
- Every faulty model exposes harmful races; every control model exposes zero harmful races (20/20 faulty sides harmful, 20/20 control sides clean).
- Execution window: 2026-11-04, 09:47–16:34 UTC (principal) and 17:06–18:23 UTC (supplementary).
- Environment (as recorded in the per-configuration provenance records): Linux x86_64 server, Docker 29.1.3 (client and server), host Python 3.14.4, RaceLoom runtime image `sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087` (`linux/amd64`), repository HEAD `ac837210b919c5b91ae3b4dd445935b5e937a083` (branch `fix/reviewer-reproducibility`). The OS release at execution time was not recorded in the provenance; the historical 2026-06 validation host was Ubuntu 24.04.3 LTS and the same server currently reports Ubuntu 26.04.1 LTS (kernel 7.0.0-42-generic).
- The five smoke configurations (`benchmarks/smoke/`) are auxiliary artifact-review checks without historical baselines; they are **not** part of the 20 baseline-backed reproductions and are not covered by the scientific checkers (see *Smoke tests* below).

## Principal matrix results (16 configurations)

Each row reports the freshly executed, checker-verified values. Branch signatures are compared order-independently; where the freshly recorded component order differs from the matrix TSV, both orders are shown and are the same multiset.

| Configuration | Depth | Branch signature (matrix TSV / recorded) | Traces (bad = control) | Harmful (bad) | Harmful (control) |
|---|---:|---|---:|---:|---:|
| B1_K8_T1_atlanta | 5 | `CBg:8;CIngress:1;CWaypoint:1;BSw:11` (both) | 156,100 | 62 | 0 |
| B1_K12_T2_nobel_eu | 4 | `CBg:12;CIngress:1;CWaypoint:1;BSw:15` (both) | 49,980 | 38 | 0 |
| B1_K14_T3_geant2012 | 4 | `CBg:14;CIngress:1;CWaypoint:1;BSw:17` / `CIngress:1;CWaypoint:1;CBg:14;BSw:17` | 82,688 | 44 | 0 |
| B1_K16_T4_germany50 | 4 | `CBg:16;CIngress:1;CWaypoint:1;BSw:19` (both) | 129,276 | 50 | 0 |
| B2_K8_T1_atlanta | 5 | `CBg:8;CRoute:1;BSw:10` (both) | 96,309 | 74 | 0 |
| B2_K12_T2_nobel_eu | 4 | `CBg:12;CRoute:1;BSw:14` (both) | 37,856 | 25 | 0 |
| B2_K14_T3_geant2012 | 4 | `CBg:14;CRoute:1;BSw:16` / `CRoute:1;CBg:14;BSw:16` | 64,800 | 29 | 0 |
| B2_K16_T4_germany50 | 4 | `CBg:16;CRoute:1;BSw:18` (both) | 104,040 | 33 | 0 |
| B3_K8_T1_atlanta | 5 | `CBg:8;CSliceA:1;CSliceB:1;BSw:11` (both) | 156,100 | 72 | 0 |
| B3_K12_T2_nobel_eu | 4 | `CBg:12;CSliceA:1;CSliceB:1;BSw:15` (both) | 49,980 | 51 | 0 |
| B3_K14_T3_geant2012 | 4 | `CBg:14;CSliceA:1;CSliceB:1;BSw:17` (both) | 82,688 | 46 | 0 |
| B3_K16_T4_germany50 | 4 | `CBg:16;CSliceA:1;CSliceB:1;BSw:19` (both) | 129,276 | 67 | 0 |
| B4_K8_T1_atlanta | 5 | `CBg:8;CDetect:1;CFailover:1;CCleanup:1;BSw:12` (both) | 242,363 | 79 | 0 |
| B4_K12_T2_nobel_eu | 4 | `CBg:12;CDetect:1;CFailover:1;CCleanup:1;BSw:16` (both) | 64,800 | 51 | 0 |
| B4_K14_T3_geant2012 | 4 | `CBg:14;CDetect:1;CFailover:1;CCleanup:1;BSw:18` (both) | 104,040 | 59 | 0 |
| B4_K16_T4_germany50 | 4 | `CBg:16;CDetect:1;CFailover:1;CCleanup:1;BSw:20` (both) | 158,840 | 67 | 0 |

All 16 configurations matched the historical expectations in `docs/final_4x4_matrix.tsv` exactly. These figures are identical to the published matrix in the top-level `README.md`.

## Supplementary S1--S4 results

| Configuration | Depth | Branch signature | Traces (bad = control) | Harmful (bad) | Harmful (control) |
|---|---:|---|---:|---:|---:|
| S1_multidomain_wrong_destination | 5 | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 | 396 | 0 |
| S2_hierarchical_extended_wrong_destination | 4 | `C1:7;C2:7;CM:2;BSw:15` | 38,478 | 31 | 0 |
| S3_multi_slice_shared_core_isolation | 5 | `C1:6;C2:6;BSw:13` | 363,024 | 104 | 0 |
| S4_multi_region_stale_reroute | 5 | `C1:5;C2:6;CM:2;BSw:12` | 150,533 | 18 | 0 |

All 4 configurations matched the historical expectations in `docs/synthetic_s1_s4_matrix.tsv` exactly.

## Bad/control comparisons

The scientific core of the artifact is the paired faulty/control design: the two models of a pair are identical except for one semantic difference (e.g. the waypoint's initial flow table in B1, the swapped route mapping in B2). In every one of the 20 baseline-backed pairs, the freshly executed faulty side exposed harmful races while the control side exposed zero, confirming that each detected race is attributable to the seeded fault rather than to the topology, the property, or the background churn.

## Cache counters (fresh runs)

Trace-generation and KATch cache hit/miss counters recorded by the fresh runs and compared against the historical logs by the checkers (all matched):

| Configuration | Side | Trace-gen hits | Trace-gen misses | KATch hits | KATch misses |
|---|---|---:|---:|---:|---:|
| B1_K8_T1_atlanta | bad | 14,923 | 819 | 316,483 | 757 |
| B1_K8_T1_atlanta | control | 14,923 | 819 | 479,871 | 757 |
| B1_K12_T2_nobel_eu | bad | 2,829 | 757 | 62,163 | 1,081 |
| B1_K12_T2_nobel_eu | control | 2,829 | 757 | 87,251 | 1,081 |
| B1_K14_T3_geant2012 | bad | 4,113 | 1,073 | 92,328 | 1,652 |
| B1_K14_T3_geant2012 | control | 4,263 | 923 | 129,847 | 1,061 |
| B1_K16_T4_germany50 | bad | 5,737 | 1,465 | 130,909 | 2,399 |
| B1_K16_T4_germany50 | control | 5,737 | 1,465 | 182,893 | 2,399 |
| B2_K8_T1_atlanta | bad | 10,399 | 412 | 87,403 | 383 |
| B2_K8_T1_atlanta | control | 10,399 | 412 | 201,231 | 383 |
| B2_K12_T2_nobel_eu | bad | 2,379 | 548 | 23,271 | 689 |
| B2_K12_T2_nobel_eu | control | 2,379 | 548 | 43,317 | 689 |
| B2_K14_T3_geant2012 | bad | 3,535 | 802 | 35,348 | 1,060 |
| B2_K14_T3_geant2012 | control | 3,535 | 802 | 65,678 | 1,060 |
| B2_K16_T4_germany50 | bad | 5,015 | 1,124 | 51,005 | 1,547 |
| B2_K16_T4_germany50 | control | 5,015 | 1,124 | 94,627 | 1,547 |
| B3_K8_T1_atlanta | bad | 15,042 | 700 | 276,501 | 655 |
| B3_K8_T1_atlanta | control | 15,042 | 700 | 479,973 | 655 |
| B3_K12_T2_nobel_eu | bad | 2,918 | 668 | 58,499 | 865 |
| B3_K12_T2_nobel_eu | control | 2,918 | 668 | 87,467 | 865 |
| B3_K14_T3_geant2012 | bad | 4,158 | 1,028 | 88,229 | 1,545 |
| B3_K14_T3_geant2012 | control | 4,158 | 1,028 | 129,363 | 1,545 |
| B3_K16_T4_germany50 | bad | 5,854 | 1,348 | 125,003 | 2,017 |
| B3_K16_T4_germany50 | control | 5,854 | 1,348 | 183,275 | 2,017 |
| B4_K8_T1_atlanta | bad | 20,874 | 1,315 | 691,833 | 1,199 |
| B4_K8_T1_atlanta | control | 21,451 | 738 | 926,490 | 456 |
| B4_K12_T2_nobel_eu | bad | 3,371 | 966 | 114,255 | 1,473 |
| B4_K12_T2_nobel_eu | control | 3,371 | 966 | 145,065 | 1,473 |
| B4_K14_T3_geant2012 | bad | 4,795 | 1,344 | 166,324 | 2,244 |
| B4_K14_T3_geant2012 | control | 4,795 | 1,344 | 210,626 | 2,244 |
| B4_K16_T4_germany50 | bad | 6,575 | 1,806 | 232,125 | 3,251 |
| B4_K16_T4_germany50 | control | 6,575 | 1,806 | 293,343 | 3,251 |
| S1_multidomain_wrong_destination | bad | 27,982 | 2,452 | 1,985,756 | 1,884 |
| S1_multidomain_wrong_destination | control | 29,051 | 1,383 | 2,187,626 | 814 |
| S2_hierarchical_extended_wrong_destination | bad | 2,168 | 948 | 108,058 | 1,574 |
| S2_hierarchical_extended_wrong_destination | control | 2,168 | 948 | 111,919 | 1,585 |
| S3_multi_slice_shared_core_isolation | bad | 28,660 | 1,774 | 1,494,612 | 1,872 |
| S3_multi_slice_shared_core_isolation | control | 29,123 | 1,311 | 1,523,567 | 1,249 |
| S4_multi_region_stale_reroute | bad | 14,963 | 1,410 | 585,682 | 1,424 |
| S4_multi_region_stale_reroute | control | 14,963 | 1,410 | 591,513 | 1,429 |

## Timing results (measurements, not criteria)

Wall-clock totals (`totalExecTime`, seconds) of the fresh runs, recorded as measurements of this specific execution on this specific host. They are **not** reproducibility criteria; the checkers never classify on timing. Historical totals from the 2026-06 sanitized validation logs are shown for context.

| Configuration | Fresh bad (s) | Fresh control (s) | Historical bad (s) | Historical control (s) |
|---|---:|---:|---:|---:|
| B1_K8_T1_atlanta | 347.1550267619996 | 362.15216651600076 | 563.535412 | 572.474434 |
| B1_K12_T2_nobel_eu | 479.01872522899976 | 502.7308406400007 | 833.762204 | 837.102106 |
| B1_K14_T3_geant2012 | 783.6497653770002 | 502.2383888889999 | 1432.474120 | 889.606072 |
| B1_K16_T4_germany50 | 1211.5296490269993 | 1232.5876370259994 | 1972.720083 | 2369.630452 |
| B2_K8_T1_atlanta | 155.2871980130003 | 160.765597566 | 286.921927 | 301.237840 |
| B2_K12_T2_nobel_eu | 295.97853369900076 | 307.21964687400214 | 523.141458 | 533.197898 |
| B2_K14_T3_geant2012 | 486.5996298610007 | 502.5363064480007 | 1208.228198 | 953.507350 |
| B2_K16_T4_germany50 | 755.2313967139999 | 777.722539327 | 1254.254325 | 1327.450590 |
| B3_K8_T1_atlanta | 267.5883978109996 | 276.8775314640043 | 488.524798 | 491.611782 |
| B3_K12_T2_nobel_eu | 379.66222251000363 | 389.45441495600244 | 660.107199 | 667.077585 |
| B3_K14_T3_geant2012 | 751.9671648939984 | 777.273541958999 | 1217.651288 | 1228.407852 |
| B3_K16_T4_germany50 | 1073.2546553020002 | 1054.8569150720032 | 1638.457789 | 1654.885645 |
| B4_K8_T1_atlanta | 519.8880151960038 | 213.9222480190001 | 916.026407 | 355.674991 |
| B4_K12_T2_nobel_eu | 720.8573766429981 | 722.0562221830005 | 1179.817474 | 1158.172184 |
| B4_K14_T3_geant2012 | 1138.2815677539984 | 1154.5860087719993 | 1821.278689 | 1879.773365 |
| B4_K16_T4_germany50 | 1795.3465185700006 | 1822.631041652996 | 2689.636385 | 2704.822722 |
| S1_multidomain_wrong_destination | 829.2273662500047 | 384.44342590600354 | 1427.731891 | 642.872147 |
| S2_hierarchical_extended_wrong_destination | 589.9047203230002 | 579.8762541639953 | 1049.240204 | 1059.224928 |
| S3_multi_slice_shared_core_isolation | 696.0641616859939 | 477.9939144039963 | 1287.352348 | 867.276945 |
| S4_multi_region_stale_reroute | 519.8649108450045 | 516.2511871290044 | 955.192787 | 965.633272 |

Aggregate fresh wall-clock time (sum of per-run `totalExecTime`): principal matrix 21,920.90689072601 s ≈ 365.35 min; supplementary group 4,593.625940707003 s ≈ 76.56 min. Per-phase timings (trace generation, Maude, KATch, analyzer) are preserved per side in each configuration's `final_stats.csv` in the evidence archive.

## Smoke tests (auxiliary, not baseline-backed)

The five smoke configurations in `benchmarks/smoke/` are small fast pairs intended as artifact-review checks. They have **no historical validation baselines**, are not covered by the scientific checkers, and are not counted among the 20 baseline-backed reproductions:

| Smoke configuration | Historical baseline | Executed in this release? |
|---|---|---|
| `b1_waypoint_order_smoke/T1_atlanta` | none | no |
| `b1_waypoint_tagged_marker_smoke/T1_atlanta` | none | no |
| `b2_route_mapping_smoke/T1_atlanta` | none | yes (default reviewer smoke test) |
| `b3_slice_isolation_twocontroller_smoke/T1_atlanta` | none | no |
| `b4_failover_stale_path_smoke/T1_atlanta` | none | no |

The executed B2 smoke pair (depth 4, BFS) matched its documented expectation exactly on Ubuntu (2026-11-03, canonical pipeline): bad traces=8, harmful=1, total 1.1708595470008731 s; control traces=8, harmful=0, total 1.1955787029983185 s; both sides reported branch signature `CRoute:1;BSw:2`. The same smoke test previously passed on macOS 26.5.1 / Apple M1 / Colima with `linux/amd64` emulation (15.824144 s / 16.730201 s). These smoke outcomes demonstrate pipeline correctness only; they are not scientific reproductions.
