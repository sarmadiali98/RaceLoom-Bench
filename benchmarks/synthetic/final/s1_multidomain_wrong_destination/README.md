# S1 — multidomain_wrong_destination_12sw

## Purpose

S1 is a larger Tier-3 reachability benchmark. It scales the independent-controller reachability scenario to two controller domains, 12 switches, 4 controllers, and four forbidden reachability relations.

The benchmark is meant to sit around the 10-minute scale on the current server at depth 4, making it substantially larger than the core A1–A4 benchmarks while still being practical to run.

## Real-world motivation

This benchmark represents a network with multiple independently controlled regions. Each controller domain can make local forwarding updates, but unsafe combinations of those updates can create global wrong-destination or cross-domain isolation violations.

This is meant to model the kind of failure that can happen when separately managed SDN regions, tenants, or administrative domains interact through shared links or boundary paths.

## Topology structure

The benchmark has two 6-switch independent-controller domains:

- Domain A: SW1A–SW6A, controlled by C1A and C2A
- Domain B: SW1B–SW6B, controlled by C1B and C2B

The two domains use distinct port spaces:

- Domain A uses ports 1–16
- Domain B uses ports 101–116

Each domain contains explicit inter-switch links and independently controlled forwarding updates.

## Forbidden reachability relations

The benchmark checks four forbidden relations in one property file:

- port 2 must not reach port 15
- port 1 must not reach port 16
- port 102 must not reach port 115
- port 101 must not reach port 116

These represent wrong-destination and cross-domain isolation violations across the two domains.

## Bad version

The bad version preserves the unsafe forwarding behavior in both controller domains.

Validated result at depth 4:

- Generated traces: 28080
- Harmful races found: 172
- Total execution time: approximately 627.8 seconds

## Control version

The control version preserves the same topology, controllers, branch structure, trace count, and properties, but neutralizes the unsafe bridge updates in both domains.

Validated result at depth 4:

- Generated traces: 28080
- Harmful races found: 0
- Total execution time: approximately 322.6 seconds

## Tier justification

S1 is Tier-3 because it has:

- 12 switches
- 4 controllers
- explicit inter-switch links
- multiple independently controlled domains
- four simultaneous forbidden reachability relations
- matched bad/control validation
- nontrivial analysis time around the 10-minute scale
