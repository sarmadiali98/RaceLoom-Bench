# Expected stats — L3/T4/K16 Germany50

Status: validated.

## Configuration

```text
benchmark: L3 waypoint / IDS bypass on SNDlib Germany50
variant: topology-aware background update churn
churn level: K=16
depth: 4
strategy: bfs
network_model_branches: CMon:1;CBg:16;BSw:18
Result
bad generated traces: 104040
bad harmful races: 33
bad KATch time: 1231.625172384316
bad total execution time: 1240.054118784028

control generated traces: 104040
control harmful races: 0
control KATch time: 672.3950380507158
control total execution time: 680.6495282490505
Interpretation

K16 depth 4 is the largest L3 topology-aware stress configuration so far. It validates the waypoint/bypass invariant on SNDlib Germany50 with 104,040 generated traces. The bad model exposes harmful IDS-bypass races, while the control model remains clean.
