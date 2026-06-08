# Scripts

This directory contains helper scripts for running, checking, and reproducing the benchmark artifact.

| Script | Purpose |
|---|---|
| `setup_raceloom_artifact.sh` | Downloads and loads the external RaceLoom Docker artifact from Zenodo. |
| `docker_smoke_test.sh` | Runs the default fast Docker smoke test. |
| `docker_run_pair.sh` | Runs one bad/control benchmark pair inside a RaceLoom Docker image. |
| `check_pair_result.py` | Checks generated logs against expected traces and harmful-race counts. |
| `extract_paper_numbers_from_logs.py` | Parses sanitized validation logs and checks reproduced numbers against committed summary TSV files. |
| `run_one_pair.sh` | Non-Docker helper for environments where RaceLoom is already installed. |
| `run_final_matrix.sh` | Batch runner for the full B1--B4 matrix. |
| `run_raceloom_progress.sh` | Compatibility placeholder; Docker scripts are preferred for artifact review. |
| `summarize_logs.py` | Helper for summarizing RaceLoom logs. |
