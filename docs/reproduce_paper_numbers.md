# Reproducing paper numbers from validation logs

This repository includes sanitized validation logs for the runs used to report the benchmark numbers.

The logs are stored under:

    docs/validation_logs/

There are 40 logs total:

- 32 logs for the B1--B4 main matrix: 16 benchmark/topology cells times faulty/control.
- 8 logs for the S1--S4 synthetic benchmarks: 4 scenarios times faulty/control.

The logs are sanitized: server-local home paths and hostnames are replaced with placeholders. The numerical RaceLoom output is preserved.

## Extract and check the numbers

From the repository root, run:

    python3 scripts/extract_paper_numbers_from_logs.py

This creates:

    reproduced_paper_numbers/reproduced_from_logs.tsv
    reproduced_paper_numbers/reproduced_final_4x4_matrix.md
    reproduced_paper_numbers/reproduced_synthetic_s1_s4_matrix.md

The script also checks the reproduced trace counts and harmful-race counts against:

    docs/final_4x4_matrix.tsv
    docs/synthetic_s1_s4_matrix.tsv

If the command exits successfully, the numerical fields in the committed result summaries are reproduced from the validation logs.

For exact per-run runtimes, use:

    docs/runtime_summary.md
    docs/benchmark_runtimes_exact.tsv

## What is not included

This repository does not include RaceLoom output directories or generated trace artifacts. Those can be large and are not needed to verify the reported aggregate numbers. The included validation logs preserve the final RaceLoom statistics needed to reproduce the paper tables: branch structure, trace count, harmful-race count, and total execution time.
