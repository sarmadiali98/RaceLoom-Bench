# Trace Validation — S4 multi_region_stale_reroute_12sw

Source core

S4 is built from the validated A4 stale-reroute benchmark:

benchmarks_journal/reachability_loop_during_reroute
Intended interpretation

The model represents a hierarchical multi-region reroute/failover setting.

The bad model exposes harmful reachability caused by a stale or unsafe reroute update.

The control model preserves safe reroute behavior.

V2 scaling

S4 adds:

SW6, SW7, SW8 to the C1-controlled regional side
SW9, SW10, SW11, SW12 to the C2-controlled regional side
extra asymmetric side-core links

These additions increase the trace space and architectural realism but do not change the intended semantic core.
