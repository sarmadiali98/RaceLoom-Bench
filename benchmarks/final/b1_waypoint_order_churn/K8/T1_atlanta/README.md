# L3/T1/K8 — Waypoint on SNDlib Atlanta with background update churn

This is the topology-aware version of the L3 waypoint benchmark.

It keeps the same core invariant:

```text
monitored traffic must not bypass the IDS waypoint

but adds eight safe background updates on topology nodes outside the core safe/bypass paths.

Expected validation:

bad: harmful races > 0
control: harmful races = 0

