# Artifact review guide

This repository contains benchmark inputs and helper scripts for RaceLoom. It does not include RaceLoom itself.

To run the benchmarks, first obtain the RaceLoom Docker artifact from the RaceLoom artifact repository or release page. Then set the image name through `RACELOOM_IMAGE`.

```bash
export RACELOOM_IMAGE=<raceLoom-image>:<tag>

If the RaceLoom Docker image uses a different working directory or command, configure:

export RACELOOM_WORKDIR=/workspace/raceloom
export RACELOOM_CMD="python main.py"
Reviewer smoke test

From the repository root:

bash scripts/docker_smoke_test.sh

The smoke test runs the S2 synthetic benchmark pair. The expected result is:

Model	Generated traces	Harmful races
S2 faulty	38,478	31
S2 control	38,478	0

A successful run ends with:

PASS
Full benchmark reruns

The full B1--B4 and S1--S4 benchmark suites can take substantially longer than the smoke test. Use the result tables in docs/ as the expected reference summaries.
