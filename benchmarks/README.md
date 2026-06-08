# Benchmarks

This directory contains the benchmark model inputs.

| Path | Contents |
|---|---|
| `benchmarks/final/` | Main B1--B4 source-derived benchmark matrix. See `benchmarks/final/README.md`. |
| `benchmarks/smoke/` | Small fast smoke benchmarks. See `benchmarks/smoke/README.md`. |
| `benchmarks/synthetic/` | S1--S4 synthetic benchmark group. See `benchmarks/synthetic/README.md`. |

Each benchmark pair contains a `bad/` model and a `control/` model. The expected interpretation is that the faulty model exposes harmful races and the control model exposes zero harmful races.
