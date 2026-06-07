# Trace Validation — S2 hierarchical_extended_wrong_destination_12sw

## Safety property

(port = 1) . @Network . (port = 8)

AllowsPackets=false

## Intended bad path

1 -> 2 -> 3 -> 6 -> 8 -> 20 -> 21 -> 22 -> 23 -> 24 -> 25 -> 26 -> 27 -> 28 -> 29 -> 30 -> 31 -> 32 -> 33 -> 34 -> 108

The key unsafe manager-triggered update is:

SW2: (port = 3) . (port <- 6)

## Control behavior

The control changes the key update to:

SW2: (port = 3) . (port <- 4)

This avoids the long forbidden path.
