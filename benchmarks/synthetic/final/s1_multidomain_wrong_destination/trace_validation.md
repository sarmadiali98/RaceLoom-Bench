# Trace Validation — S1 multidomain_wrong_destination_12sw

## Safety property

The benchmark checks four forbidden reachability relations:

- (port=2) . @Network . (port=15)
- (port=1) . @Network . (port=16)
- (port=102) . @Network . (port=115)
- (port=101) . @Network . (port=116)

Each relation is forbidden with AllowsPackets=false.

## Bad model

The bad model contains unsafe bridge/reroute updates in both independent-controller domains. These updates can combine with existing links and switch rules to create forbidden end-to-end paths.

RaceLoom reports 172 harmful races at depth 4.

## Control model

The control model keeps the same 12-switch / 4-controller structure and the same forbidden relations, but changes the unsafe bridge updates to safe alternatives.

RaceLoom reports zero harmful races at depth 4.

## Validation conclusion

The harmful races in the bad model are caused by the intended wrong-destination and isolation-violating updates, not by a malformed property or by a reduced control trace space.
