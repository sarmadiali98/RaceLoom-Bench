# B2 wrong next-hop / route mapping — T1 Atlanta

This directory contains the B2 route-mapping benchmark instance on the T1 Atlanta topology.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `source/` | Source/embedding metadata for this benchmark instance. |
| `metadata.json` | Recorded benchmark metadata. |
| `run.sh` | Local helper script for this instance. |

Expected counted result: 96,309 traces, 74 harmful races in the faulty model, and 0 harmful races in the control model.
