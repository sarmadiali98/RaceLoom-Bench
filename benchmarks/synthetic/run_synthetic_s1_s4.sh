#!/usr/bin/env bash
set -euo pipefail

bash benchmarks/synthetic/final/s1_multidomain_wrong_destination/run_s1.sh 5 bfs
bash benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination/run_s2.sh 4 bfs
bash benchmarks/synthetic/final/s3_multi_slice_shared_core_isolation/run_s3.sh 5 bfs
bash benchmarks/synthetic/final/s4_multi_region_stale_reroute/run_s4.sh 5 bfs
