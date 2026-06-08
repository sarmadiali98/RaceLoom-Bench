# Main B1--B4 benchmark matrix

This directory contains the main source-derived benchmark matrix.

| Path | Family | Description |
|---|---|---|
| `b1_waypoint_order_churn/` | B1 waypoint / IDS-bypass | Monitored traffic must traverse the required waypoint. |
| `b2_route_mapping_forced_distinct/` | B2 wrong next-hop / route update | Routed traffic must not reach the wrong next-hop branch. |
| `b3_slice_isolation_twocontroller_churn/` | B3 slice isolation | Traffic from one slice must not reach another slice. |
| `b4_failover_cleanup_churn/` | B4 failover / stale path | Post-failure traffic must not continue along a stale failed path. |

Each family is evaluated on the selected topologies under `K*/T*/{bad,control}` directories. The result matrix is summarized in `docs/final_4x4_matrix.md`.
