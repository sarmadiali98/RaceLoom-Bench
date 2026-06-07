# S3 — multi_slice_shared_core_isolation_12sw

## Purpose

S3 is a larger synthetic tenant/slice-isolation benchmark.

It keeps the validated A3 isolation-violation core and scales the surrounding network into a larger multi-slice/shared-core topology.

## Structure

- 12 switches
- 2 independent controllers
- two tenant/slice regions
- extra internal slice paths
- extra shared-core side links
- same bad/control isolation invariant as A3

## Real-world motivation

This models a multi-tenant or network-slicing setting where independently controlled slice regions share some physical/core infrastructure. A bad update can leak traffic across a protected slice boundary, while the control version preserves isolation.

## Bad version

The bad version preserves the original A3 isolation-violation behavior and adds larger surrounding slice/core structure.

Expected behavior:

```text
Harmful races found: > 0
Control version

The control version preserves the same topology size and controller structure, but uses the safe update behavior from the validated A3 control model.

Expected behavior:

Harmful races found: 0
Recommended command
bash benchmarks_synthetic/final/s3_multi_slice_shared_core_isolation/run_a3_v2.sh 5 bfs

