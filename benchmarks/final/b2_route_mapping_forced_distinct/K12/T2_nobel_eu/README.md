# B2 wrong next-hop / route mapping — T2 Nobel-EU

This directory contains the B2 route-mapping benchmark instance on the T2 Nobel-EU topology.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `source/` | Source/embedding metadata for this benchmark instance. |
| `metadata.json` | Recorded benchmark metadata. |
| `run.sh` | Local helper script for this instance. |

Expected counted result: 37,856 traces, 25 harmful races in the faulty model, and 0 harmful races in the control model.
