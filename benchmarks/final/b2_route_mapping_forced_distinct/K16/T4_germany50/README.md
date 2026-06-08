# B2 wrong next-hop / route mapping — T4 Germany50

This directory contains the B2 route-mapping benchmark instance on the T4 Germany50 topology.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `source/` | Source/embedding metadata for this benchmark instance. |
| `metadata.json` | Recorded benchmark metadata. |
| `run.sh` | Local helper script for this instance. |

Expected counted result: 104,040 traces, 33 harmful races in the faulty model, and 0 harmful races in the control model.
