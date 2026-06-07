# Expected Stats — S3 multi_slice_shared_core_isolation_12sw

Status: pending validation.

Recommended command:

bash benchmarks_synthetic/final/s3_multi_slice_shared_core_isolation/run_a3_v2.sh 5 bfs

Expected behavior:

Bad version: harmful races greater than zero
Control version: harmful races equal to zero
Bad and control should have comparable branch structure and trace counts
