# Expected Stats — S1 multidomain_wrong_destination_12sw

## Recommended run

```bash
bash benchmarks/synthetic/final/s1_multidomain_wrong_destination/run_s1.sh 5 bfs
Bad version

Validated on 2026-05-24 at depth 5:

Network model branches: C1A:3; C2A:3; C1B:3; C2B:3; BSw:13
Generated traces: 363024
Trace generation time: 12.381033284007572 seconds
Maude execution time: 2.7701479155221023 seconds
Trace generation cache hits: 27982
Trace generation cache misses: 2452
KATch total execution time: 1350.2849128727103 seconds
KATch total cache hits: 1985756
KATch total cache misses: 1884
Harmful races found: 396
Trace Analyzer execution time: 1377.812679554976 seconds
Total execution time: 1390.1937128389836 seconds
Control version

Validated on 2026-05-24 at depth 5:

Network model branches: C1A:3; C2A:3; C1B:3; C2B:3; BSw:13
Generated traces: 363024
Trace generation time: 10.582543096970767 seconds
Maude execution time: 1.595638758444693 seconds
Trace generation cache hits: 29051
Trace generation cache misses: 1383
KATch total execution time: 591.4027784478967 seconds
KATch total cache hits: 2187626
KATch total cache misses: 814
Harmful races found: 0
Trace Analyzer execution time: 617.4730976740248 seconds
Total execution time: 628.0556407709955 seconds
Interpretation

The bad and control versions have the same generated trace count and branch structure. The bad model exposes 396 harmful races, while the control model exposes zero harmful races.
