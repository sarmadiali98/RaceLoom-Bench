# S4 — multi_region_stale_reroute_12sw

## Purpose

S4 is a larger synthetic stale-reroute / failover benchmark.

It keeps the validated A4 stale-reroute semantic core and scales the surrounding network into a larger multi-region topology.

## Structure

- 12 switches
- 3 controllers
  - lower controller C1
  - lower controller C2
  - manager controller CM
- two lower-controller regions
- extra regional reroute corridors
- asymmetric inter-region side-core links
- same bad/control reroute invariant as A4

## Real-world motivation

This models a hierarchical SDN reroute or failover setting where regional controllers update different parts of the network under a manager controller. A stale or unsafe reroute update can expose harmful reachability, while the control version preserves the intended safe routing behavior.

## Bad version

The bad version preserves the original A4 stale-reroute behavior and adds larger surrounding regional/core structure.

Expected behavior:

```text
Harmful races found: > 0
Control version

The control version preserves the same topology size and controller structure, but uses the safe update behavior from the validated A4 control model.

Expected behavior:

Harmful races found: 0
Recommended command
bash benchmarks_synthetic/final/s4_multi_region_stale_reroute/run_a4_v2.sh 5 bfs

