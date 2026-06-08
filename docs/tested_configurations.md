
Tested configurations

This file records the systems used to generate and check the benchmark results.

Full benchmark generation / validation server
OS: Ubuntu 24.04.3 LTS
Kernel: Linux 6.8.0-87-generic x86_64
Memory: approximately 128 GB RAM
RaceLoom execution: RaceLoom artifact environment with KATch
Strategy: BFS
Main B1--B4 matrix: see docs/final_4x4_matrix.md
Synthetic S1--S4 matrix: see docs/synthetic_s1_s4_matrix.md
Reviewer smoke test

To be filled after testing from a clean Ubuntu machine with Docker.

Machine	OS	Docker	Command	Runtime	Result
TBD	TBD	TBD	bash scripts/docker_smoke_test.sh	TBD	TBD
EOF					

cat > docs/references.md <<'EOF'

References

This benchmark repository is a companion artifact for RaceLoom.

RaceLoom
RaceLoom paper: TODO
RaceLoom artifact repository / release: TODO
RaceLoom Docker image: TODO
RaceLoom-Bench
Repository: https://github.com/sarmadiali98/RaceLoom-Bench

If you use this benchmark suite, please cite the RaceLoom paper and this repository. Full bibliographic details should be updated after publication.
