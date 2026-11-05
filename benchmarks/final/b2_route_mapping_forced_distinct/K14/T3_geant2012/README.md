# B2 wrong next-hop / route mapping — T3 Geant2012

This directory contains the B2 route-mapping benchmark instance on the T3 Geant2012 topology.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `source/` | Source/embedding metadata for this benchmark instance. |
| `metadata.json` | Recorded benchmark metadata. |

Expected counted result: 64,800 traces, 29 harmful races in the faulty model, and 0 harmful races in the control model.

This is the `B2_route_mapping  T3_geant2012  K14  4  CBg:14;CRoute:1;BSw:16  64800  29  0` row of `docs/final_4x4_matrix.tsv`. The historical evidence is `docs/validation_logs/main/B2_K14_T3_geant2012_bad.txt` and `docs/validation_logs/main/B2_K14_T3_geant2012_control.txt` (dated 2026-06-05). The configuration was independently re-executed through the canonical pipeline on 2026-11-04 and classified `SCIENTIFIC_MATCH` by `scripts/check_final_matrix.py`; see `docs/RESULTS.md`.

Run through the canonical pipeline:

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_MATRIX_OUTPUT_ROOT=/path/to/evidence-root
export RACELOOM_MATRIX_ONLY=B2_K14_T3_geant2012
bash scripts/run_final_matrix.sh
```

See `docs/REPRODUCTION.md` and `docs/VALIDATION.md`.
