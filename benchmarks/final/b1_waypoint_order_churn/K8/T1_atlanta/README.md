# B1 waypoint / IDS-bypass — T1 Atlanta

This directory contains the B1 waypoint-order benchmark instance on the T1 Atlanta topology.

Contents:

| Path | Contents |
|---|---|
| `bad/` | Faulty RaceLoom model and property. |
| `control/` | Corrected RaceLoom model and property. |
| `source/` | Source/embedding metadata for this benchmark instance. |
| `metadata.json` | Recorded benchmark metadata. |
| `run.sh` | Local helper script for this instance. |

Expected counted result: 156,100 traces, 62 harmful races in the faulty model, and 0 harmful races in the control model.
