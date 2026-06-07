# Expected stats — L3/T1/K8 Atlanta

Status: validated.

## Configuration

```text
benchmark: L3 waypoint / IDS bypass on SNDlib Atlanta
variant: topology-aware background update churn
churn level: K=8
depth: 4
strategy: bfs
network_model_branches: CMon:1;CBg:8;BSw:10
Result
bad generated traces: 9720
bad harmful races: 17
bad total execution time: 167.1105082980357

control generated traces: 9720
control harmful races: 0
control total execution time: 95.67762753402349
Interpretation

K8 depth 4 is a medium-large topology-aware configuration. Compared with K4 depth 4, it increases the dynamic update space from CMon:1;CBg:4;BSw:6 to CMon:1;CBg:8;BSw:10.

The bad model exposes IDS-bypass races. The control model remains clean.
