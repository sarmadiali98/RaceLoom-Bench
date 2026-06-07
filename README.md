# RaceLoom-Bench

This repository contains a curated RaceLoom benchmark suite with a completed 4×4 counted evaluation matrix.

## Counted benchmark families

- B1: waypoint / IDS-bypass update-order race
- B2: wrong next-hop / route-mapping race
- B3: two-controller slice-isolation race
- B4: failover-cleanup / stale-path race

## Topologies

- T1: SNDlib Atlanta
- T2: SNDlib Nobel-EU
- T3: Topology Zoo Geant2012
- T4: SNDlib Germany50

## Result matrix

See:

- `docs/final_4x4_matrix.md`
- `docs/final_4x4_matrix.tsv`

All 16 bad models expose harmful races. All 16 control models have zero harmful races.

## Layout

```text
benchmarks/final/        final counted 4×4 benchmark models
benchmarks/smoke/        selected smoke tests
topology_assets/         topology JSON assets
tools/generators/        generation scripts
tools/audits/            audit scripts
scripts/                 run and summary scripts
docs/                    matrix and documentation notes
Running one benchmark pair
scripts/run_one_pair.sh benchmarks/final/b1_waypoint_order_churn/K8/T1_atlanta 5 results
Running the full matrix
scripts/run_final_matrix.sh results/final_matrix_logs
python3 scripts/summarize_logs.py results/final_matrix_logs

## Synthetic S1--S4 benchmarks

In addition to the source-derived B1--B4 topology matrix, the repository includes a curated S1--S4 synthetic benchmark set. These benchmarks are fixed synthetic RaceLoom scenarios with paired faulty and control models.

| ID | Scenario | Depth / strategy | Branch structure | Result |
|---|---|---:|---|---:|
| S1 | Multidomain wrong destination | 5 / bfs | `C1A:3;C2A:3;C1B:3;C2B:3;BSw:13` | 363,024 / 396 / 0 |
| S2 | Hierarchical extended wrong destination | 4 / bfs | `C1:7;C2:7;CM:2;BSw:15` | 38,478 / 31 / 0 |
| S3 | Multi-slice shared-core isolation | 5 / bfs | `C1:6;C2:6;BSw:13` | 363,024 / 104 / 0 |
| S4 | Multi-region stale reroute | 5 / bfs | `C1:5;C2:6;CM:2;BSw:12` | 150,533 / 18 / 0 |

The result format is `generated traces / faulty harmful races / control harmful races`. All four faulty synthetic models expose harmful races, and all four control models expose zero harmful races.

Synthetic models: `benchmarks/synthetic/final/`

Synthetic result summaries:

- `docs/synthetic_s1_s4_matrix.md`
- `docs/synthetic_s1_s4_matrix.tsv`

To run the full synthetic set:

    bash benchmarks/synthetic/run_synthetic_s1_s4.sh

Individual synthetic benchmarks can also be run from their own directories, for example:

    bash benchmarks/synthetic/final/s1_multidomain_wrong_destination/run_s1.sh 5 bfs
