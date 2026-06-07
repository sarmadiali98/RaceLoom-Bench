# S2 — hierarchical_extended_wrong_destination_12sw

## Purpose

S2 is a larger hierarchy-compatible reachability benchmark.

It keeps RaceLoom's original working two-level hierarchy:

CM -> C1/C2 -> switches

and extends the data-plane topology to 12 switches with a long asymmetric transit path.

## Structure

- 12 switches
- 3 controllers: C1, C2, CM
- working two-level hierarchy
- explicit inter-switch links
- long asymmetric transit path
- one forbidden reachability property

## Forbidden relation

Traffic entering at port 1 must not reach port 8:

(port = 1) . @Network . (port = 8)

AllowsPackets: false

## Bad version

The bad version lets CM trigger C2 to install this SW2 update:

(port = 3) . (port <- 6)

That sends traffic into a long path ending at forbidden port 8.

## Control version

The control version uses:

(port = 3) . (port <- 4)

which sends traffic away from the long forbidden path.
