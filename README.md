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

