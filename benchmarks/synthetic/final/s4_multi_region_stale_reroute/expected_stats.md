# Expected Stats — multi_region_stale_reroute_12sw

## Recommended run

```bash
bash benchmarks/synthetic/final/s4_multi_region_stale_reroute/run_s4.sh 5 bfs
Bad version

Validated on 2026-05-24;19:42:41 at depth 5:

Network model branches: C1:5;C2:6;CM:2;BSw:12
Generated traces: 150533
Trace generation time: 11.393642176990397 seconds
Maude execution time: 5.965923148149159 seconds
Trace generation cache hits: 14963
Trace generation cache misses: 1410
KATch total execution time: 913.9535014847643 seconds
KATch total cache hits: 585682
KATch total cache misses: 1424
Harmful races found: 18
Trace Analyzer execution time: 923.8298014100292 seconds
Total execution time: 935.2234435870196 seconds
Control version

Validated on 2026-05-24;19:58:18 at depth 5:

Network model branches: C1:5;C2:6;CM:2;BSw:12
Generated traces: 150533
Trace generation time: 11.329583516984712 seconds
Maude execution time: 5.906745502841659 seconds
Trace generation cache hits: 14963
Trace generation cache misses: 1410
KATch total execution time: 916.4796599623514 seconds
KATch total cache hits: 591513
KATch total cache misses: 1429
Harmful races found: 0
Trace Analyzer execution time: 926.38947159698 seconds
Total execution time: 937.7190551139647 seconds
Interpretation

The bad and control versions have the same generated trace count and branch structure. The bad model exposes harmful races, while the control model exposes zero harmful races.
