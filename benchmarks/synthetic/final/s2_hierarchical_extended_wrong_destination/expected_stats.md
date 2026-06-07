# Expected Stats — S2 hierarchical_extended_wrong_destination_12sw

## Recommended run

```bash
bash benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination/run_s2.sh 4 bfs
Bad version

Observed on 2026-05-24 at depth 4:

Network model branches: C1:7; C2:7; CM:2; BSw:15
Generated traces: 38478
Trace generation time: 10.875066605047323 seconds
Maude execution time: 6.222786183701828 seconds
Trace generation cache hits: 2168
Trace generation cache misses: 948
KATch total execution time: 1004.5828951910953 seconds
KATch total cache hits: 108058
KATch total cache misses: 1574
Harmful races found: 31
Trace Analyzer execution time: 1007.9317614120082 seconds
Total execution time: 1018.8068280170555 seconds
Control version

Observed on 2026-05-24 at depth 4:

Network model branches: C1:7; C2:7; CM:2; BSw:15
Generated traces: 38478
Trace generation time: 10.923202387988567 seconds
Maude execution time: 6.428357926604804 seconds
Trace generation cache hits: 2168
Trace generation cache misses: 948
KATch total execution time: 1024.2826083498076 seconds
KATch total cache hits: 111919
KATch total cache misses: 1585
Harmful races found: 0
Trace Analyzer execution time: 1027.5635939670028 seconds
Total execution time: 1038.4867963549914 seconds
Interpretation

The bad and control versions have the same generated trace count and the same branch structure. The bad model exposes 31 harmful races, while the control model exposes zero harmful races. This validates that the harmful races are caused by the intended unsafe hierarchical update rather than by a difference in trace-space size.
