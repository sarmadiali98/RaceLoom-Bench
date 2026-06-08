# RaceLoom-Bench

RaceLoom-Bench is a curated benchmark suite for evaluating RaceLoom on software-defined networking race conditions. The repository contains paired faulty/control RaceLoom models, forwarding properties, topology assets, run scripts, and recorded result summaries.

The benchmark suite has two parts:

1. `B1`--`B4`: source-derived benchmark families embedded into four selected network topologies.
2. `S1`--`S4`: fixed synthetic benchmark scenarios with paired faulty/control models.

In every benchmark pair, the faulty model is expected to expose harmful races, while the corresponding control model is expected to expose zero harmful races.

## Repository layout

```text
benchmarks/final/
  b1_waypoint_order_churn/
  b2_route_mapping_forced_distinct/
  b3_slice_isolation_twocontroller_churn/
  b4_failover_cleanup_churn/

benchmarks/synthetic/final/
  s1_multidomain_wrong_destination/
  s2_hierarchical_extended_wrong_destination/
  s3_multi_slice_shared_core_isolation/
  s4_multi_region_stale_reroute/

docs/
  final_4x4_matrix.md
  final_4x4_matrix.tsv
  synthetic_s1_s4_matrix.md
  synthetic_s1_s4_matrix.tsv

scripts/
  run_one_pair.sh
  run_final_matrix.sh
  run_raceloom_progress.sh
  summarize_logs.py

topology_assets/
  T1_atlanta.json
  T2_nobel_eu.json
  T3_geant2012.json
  T4_germany50.json
  selected_topologies.json
Main B1--B4 benchmark matrix

The main benchmark matrix contains four source-derived SDN race families evaluated on four topologies.

ID	Family	Checked property
B1	Waypoint / IDS-bypass	Monitored traffic must traverse the required waypoint.
B2	Wrong next-hop / route update	Routed traffic must not reach an incorrect next-hop branch.
B3	Slice isolation	Traffic from one slice must not reach another slice.
B4	Failover / stale path	Post-failure traffic must not continue along a stale failed path.

The four selected topologies are:

Topology	Source	Nodes	Edges
T1 Atlanta	SNDlib	15	22
T2 Nobel-EU	SNDlib	28	41
T3 Geant2012	Topology Zoo	40	61
T4 Germany50	SNDlib	50	88
Main matrix results

Each entry reports generated traces / faulty harmful races / control harmful races.

Benchmark	T1 Atlanta	T2 Nobel-EU	T3 Geant2012	T4 Germany50
B1 waypoint / IDS-bypass	156,100 / 62 / 0	49,980 / 38 / 0	82,688 / 44 / 0	129,276 / 50 / 0
B2 wrong next-hop / route mapping	96,309 / 74 / 0	37,856 / 25 / 0	64,800 / 29 / 0	104,040 / 33 / 0
B3 slice isolation	156,100 / 72 / 0	49,980 / 51 / 0	82,688 / 46 / 0	129,276 / 67 / 0
B4 failover / stale path	242,363 / 79 / 0	64,800 / 51 / 0	104,040 / 59 / 0	158,840 / 67 / 0

All 16 faulty models expose harmful races. All 16 control models expose zero harmful races.

The same results are also available in:

docs/final_4x4_matrix.md
docs/final_4x4_matrix.tsv
Synthetic S1--S4 benchmarks

The repository also includes a curated S1--S4 synthetic benchmark set. These are fixed synthetic RaceLoom scenarios with paired faulty/control models.

ID	Scenario	Depth	Strategy	Generated traces	Faulty harmful races	Control harmful races
S1	Multidomain wrong destination	5	bfs	363,024	396	0
S2	Hierarchical extended wrong destination	4	bfs	38,478	31	0
S3	Multi-slice shared-core isolation	5	bfs	363,024	104	0
S4	Multi-region stale reroute	5	bfs	150,533	18	0

All four faulty synthetic models expose harmful races. All four control models expose zero harmful races.

The branch structures for the synthetic runs are:

ID	Branch structure
S1	C1A:3;C2A:3;C1B:3;C2B:3;BSw:13
S2	C1:7;C2:7;CM:2;BSw:15
S3	C1:6;C2:6;BSw:13
S4	C1:5;C2:6;CM:2;BSw:12

The same results are also available in:

docs/synthetic_s1_s4_matrix.md
docs/synthetic_s1_s4_matrix.tsv
Running benchmarks

This repository contains RaceLoom benchmark inputs and helper scripts. It assumes that RaceLoom itself is available in the execution environment.

A benchmark pair consists of:

bad/model.json
bad/properties.json
control/model.json
control/properties.json
Run one main benchmark pair

Example: B4 on Germany50.

bash scripts/run_one_pair.sh benchmarks/final/b4_failover_cleanup_churn/K16/T4_germany50 4 results
Run the full B1--B4 matrix
bash scripts/run_final_matrix.sh
Run the synthetic S1--S4 set
bash benchmarks/synthetic/run_synthetic_s1_s4.sh
Run one synthetic benchmark

Example: S1.

bash benchmarks/synthetic/final/s1_multidomain_wrong_destination/run_s1.sh 5 bfs
Expected interpretation

For each benchmark pair:

the faulty model should produce at least one harmful race;
the control model should produce zero harmful races;
both models in a pair use the same forwarding property and comparable exploration settings.

This paired design is intended to make the result easy to interpret. A successful run is not just one in which RaceLoom finds a harmful trace. It is one in which the harmful behavior appears in the faulty model and disappears in the corresponding corrected model.

Scope

These benchmarks are RaceLoom model-level artifacts. They are source-derived or synthetic abstractions of SDN race scenarios, not full executions of production SDN controllers. Symbolic ports in the models represent traffic classes, decision points, safe outcomes, and forbidden outcomes; they should not always be read as physical switch ports.

Citation

If you use this benchmark suite, cite the associated RaceLoom paper and this repository.

Setting up RaceLoom

This repository does not include RaceLoom itself. To run the benchmarks, first download and load the RaceLoom Docker artifact from Zenodo:

bash scripts/setup_raceloom_artifact.sh

Then configure the benchmark scripts:

export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
export RACELOOM_CMD="python main.py"

On Apple Silicon Macs, also set:

export DOCKER_PLATFORM=linux/amd64

After setup, run the reviewer smoke test:

bash scripts/docker_smoke_test.sh

The RaceLoom artifact record is available at https://doi.org/10.5281/zenodo.16884345.

## Runtime summary

The full B1--B4 matrix and S1--S4 synthetic benchmarks were validated on the server configuration recorded in `docs/tested_configurations.md`.

- Main B1--B4 matrix runtimes are summarized in `docs/runtime_summary.md`.
- Synthetic S1--S4 runtimes are summarized in `docs/runtime_summary.md`.
- The reviewer smoke test is intentionally much smaller and is documented in `docs/artifact_review.md`.

The smoke test is the recommended first reviewer check. Full benchmark reruns are intended for a native Ubuntu/Linux amd64 machine or a comparable workstation/server.
