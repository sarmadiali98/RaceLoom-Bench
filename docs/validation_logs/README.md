# Validation logs

This directory contains sanitized RaceLoom validation logs used to reproduce the reported benchmark numbers.

| Path | Contents |
|---|---|
| `main/` | B1--B4 validation logs: 16 benchmark/topology cells times faulty/control. |
| `synthetic/` | S1--S4 validation logs: 4 synthetic scenarios times faulty/control. |

There are 40 validation log files with the `.txt` extension. Server-local paths and hostnames have been replaced with placeholders. The numerical RaceLoom output is preserved.

Use the following command from the repository root to reproduce and check the reported numbers:

    python3 scripts/extract_paper_numbers_from_logs.py

See `docs/reproduce_paper_numbers.md` for details.
