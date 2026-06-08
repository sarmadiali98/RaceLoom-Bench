# Smoke benchmarks

This directory contains small RaceLoom benchmark pairs for fast artifact-review checks.

| Path | Purpose |
|---|---|
| `b1_waypoint_order_smoke/T1_atlanta/` | Small B1 waypoint-order smoke benchmark. |
| `b1_waypoint_tagged_marker_smoke/T1_atlanta/` | Small B1 tagged-marker smoke benchmark. |
| `b2_route_mapping_smoke/T1_atlanta/` | Small B2 route-mapping smoke benchmark used by `scripts/docker_smoke_test.sh`. |
| `b3_slice_isolation_twocontroller_smoke/T1_atlanta/` | Small B3 two-controller slice-isolation smoke benchmark. |
| `b4_failover_stale_path_smoke/T1_atlanta/` | Small B4 stale-failover smoke benchmark. |

The default reviewer smoke test is `b2_route_mapping_smoke/T1_atlanta` at depth 4 with BFS. It should produce 8 traces, 1 harmful race in the faulty model, and 0 harmful races in the control model.
