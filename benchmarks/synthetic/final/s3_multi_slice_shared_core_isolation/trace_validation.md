# Trace Validation — S3 multi_slice_shared_core_isolation_12sw

Source core

S3 is built from the validated A3 isolation benchmark:

benchmarks_journal/reachability_blackhole_during_migration
Intended interpretation

The model represents two independently controlled tenant/slice regions.

The bad model exposes forbidden cross-slice reachability.

The control model preserves slice isolation.

V2 scaling

S3 adds:

SW7, SW8, SW9 to the C1-controlled slice side
SW10, SW11, SW12 to the C2-controlled slice side
extra side-core/shared-core links

These additions increase the trace space and architectural realism but do not change the intended semantic core.
