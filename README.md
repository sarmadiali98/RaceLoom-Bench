# RaceLoom-Bench

RaceLoom-Bench is a benchmark artifact for evaluating RaceLoom on software-defined networking race conditions. It contains RaceLoom model inputs, forwarding properties, topology assets, run scripts, smoke tests, and expected result summaries.

This repository does **not** include RaceLoom itself. RaceLoom is distributed separately through the RaceLoom artifact record:

- RaceLoom artifact DOI: https://doi.org/10.5281/zenodo.16884345
- RaceLoom artifact download: https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1
- RaceLoom repository: https://github.com/andreioff/RaceLoom

## Artifact at a glance

| Part | Path | Purpose |
|---|---|---|
| Main benchmark matrix | `benchmarks/final/` | Source-derived B1--B4 benchmark families on four selected topologies. |
| Smoke benchmarks | `benchmarks/smoke/` | Small fast benchmarks for artifact-review checks. |
| Synthetic benchmarks | `benchmarks/synthetic/final/` | Curated S1--S4 synthetic benchmark set. |
| Result summaries | `docs/` | Matrix results, runtime summaries, tested configurations, and artifact-review notes. |
| Runner scripts | `scripts/` | Docker wrapper scripts, smoke-test scripts, and result checkers. |
| Topology assets | `topology_assets/` | Selected topology JSON assets and topology metadata. |

In each benchmark pair, the faulty model is expected to expose harmful races, while the corresponding control model is expected to expose zero harmful races.

## Repository layout

```text
RaceLoom-Bench/
├── README.md
├── LICENSE
├── benchmarks/
│   ├── README.md
│   ├── final/
│   │   ├── README.md
│   │   ├── b1_waypoint_order_churn/
│   │   ├── b2_route_mapping_forced_distinct/
│   │   ├── b3_slice_isolation_twocontroller_churn/
│   │   └── b4_failover_cleanup_churn/
│   ├── smoke/
│   │   ├── README.md
│   │   ├── b1_waypoint_order_smoke/
│   │   ├── b1_waypoint_tagged_marker_smoke/
│   │   ├── b2_route_mapping_smoke/
│   │   ├── b3_slice_isolation_twocontroller_smoke/
│   │   └── b4_failover_stale_path_smoke/
│   └── synthetic/
│       ├── README.md
│       ├── run_synthetic_s1_s4.sh
│       └── final/
│           ├── README.md
│           ├── s1_multidomain_wrong_destination/
│           ├── s2_hierarchical_extended_wrong_destination/
│           ├── s3_multi_slice_shared_core_isolation/
│           └── s4_multi_region_stale_reroute/
├── docs/
│   ├── README.md
│   ├── artifact_review.md
│   ├── final_4x4_matrix.md
│   ├── final_4x4_matrix.tsv
│   ├── references.md
│   ├── runtime_summary.md
│   ├── synthetic_s1_s4_matrix.md
│   ├── synthetic_s1_s4_matrix.tsv
│   └── tested_configurations.md
├── scripts/
│   ├── README.md
│   ├── check_pair_result.py
│   ├── docker_run_pair.sh
│   ├── docker_smoke_test.sh
│   ├── run_final_matrix.sh
│   ├── run_one_pair.sh
│   ├── run_raceloom_progress.sh
│   ├── setup_raceloom_artifact.sh
│   └── summarize_logs.py
└── topology_assets/
    ├── README.md
    ├── selected_topologies.json
    ├── T1_atlanta.json
    ├── T2_nobel_eu.json
    ├── T3_geant2012.json
    └── T4_germany50.json
```

## README index

Each subdirectory README describes the files immediately below it.

| README | Contains |
|---|---|
| `benchmarks/README.md` | Overview of final, smoke, and synthetic benchmark groups. |
| `benchmarks/final/README.md` | B1--B4 source-derived benchmark matrix layout. |
| `benchmarks/smoke/README.md` | Fast smoke benchmarks used for artifact-review checks. |
| `benchmarks/synthetic/README.md` | Synthetic benchmark group and batch runner. |
| `benchmarks/synthetic/final/README.md` | S1--S4 synthetic benchmark descriptions and per-benchmark README links. |
| `docs/README.md` | Result summaries, runtime summaries, references, and tested configurations. |
| `scripts/README.md` | Runner scripts, Docker wrappers, and checking utilities. |
| `topology_assets/README.md` | Selected topology assets and their sources. |

## Installing Docker

The artifact-review path uses Docker. RaceLoom itself is supplied as a Docker image through the RaceLoom artifact record.

### Ubuntu

A typical Docker installation on Ubuntu is:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

docker --version
docker run hello-world
```

If Docker is already installed, the last two commands are enough to check it.

### macOS

On macOS, use either Docker Desktop or Colima.

With Colima:

```bash
brew install docker colima
colima start
docker version
```

On Apple Silicon Macs, if the RaceLoom image is provided only for `linux/amd64`, set:

```bash
export DOCKER_PLATFORM=linux/amd64
```

This works for smoke testing, but the runtime is not representative of native Linux/amd64 execution.

## Setting up RaceLoom

Download and load the external RaceLoom Docker artifact:

```bash
bash scripts/setup_raceloom_artifact.sh
```

Then configure the benchmark scripts:

```bash
export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
export RACELOOM_CMD="python main.py"
```

On Apple Silicon Macs, also set:

```bash
export DOCKER_PLATFORM=linux/amd64
```

## Recommended reviewer path

From a clean machine with Docker:

```bash
git clone https://github.com/sarmadiali98/RaceLoom-Bench.git
cd RaceLoom-Bench

bash scripts/setup_raceloom_artifact.sh

export RACELOOM_IMAGE=raceloom:latest
export RACELOOM_WORKDIR=/raceloom
export RACELOOM_CMD="python main.py"

bash scripts/docker_smoke_test.sh
```

On Apple Silicon Macs, add this before running the smoke test:

```bash
export DOCKER_PLATFORM=linux/amd64
```

The smoke test runs a small B2 route-mapping benchmark pair.

Expected result:

| Model | Generated traces | Harmful races |
|---|---:|---:|
| B2 smoke faulty | 8 | 1 |
| B2 smoke control | 8 | 0 |

A successful run ends with:

```text
PASS
bad:     traces=8 harmful=1
control: traces=8 harmful=0
```

## Main B1--B4 benchmark matrix

The main benchmark matrix contains four source-derived SDN race families evaluated on four selected topologies.

| ID | Family | Checked property |
|---|---|---|
| B1 | Waypoint / IDS-bypass | Monitored traffic must traverse the required waypoint. |
| B2 | Wrong next-hop / route update | Routed traffic must not reach an incorrect next-hop branch. |
| B3 | Slice isolation | Traffic from one slice must not reach another slice. |
| B4 | Failover / stale path | Post-failure traffic must not continue along a stale failed path. |

Each entry reports `generated traces / faulty harmful races / control harmful races`.

| Benchmark | T1 Atlanta | T2 Nobel-EU | T3 Geant2012 | T4 Germany50 |
|---|---:|---:|---:|---:|
| B1 waypoint / IDS-bypass | 156,100 / 62 / 0 | 49,980 / 38 / 0 | 82,688 / 44 / 0 | 129,276 / 50 / 0 |
| B2 wrong next-hop / route mapping | 96,309 / 74 / 0 | 37,856 / 25 / 0 | 64,800 / 29 / 0 | 104,040 / 33 / 0 |
| B3 slice isolation | 156,100 / 72 / 0 | 49,980 / 51 / 0 | 82,688 / 46 / 0 | 129,276 / 67 / 0 |
| B4 failover / stale path | 242,363 / 79 / 0 | 64,800 / 51 / 0 | 104,040 / 59 / 0 | 158,840 / 67 / 0 |

All 16 faulty models expose harmful races. All 16 control models expose zero harmful races.

## Synthetic S1--S4 benchmarks

The repository also includes a curated S1--S4 synthetic benchmark set. These are fixed synthetic RaceLoom scenarios with paired faulty/control models.

| ID | Scenario | Depth | Strategy | Generated traces | Faulty harmful races | Control harmful races |
|---|---|---:|---|---:|---:|---:|
| S1 | Multidomain wrong destination | 5 | bfs | 363,024 | 396 | 0 |
| S2 | Hierarchical extended wrong destination | 4 | bfs | 38,478 | 31 | 0 |
| S3 | Multi-slice shared-core isolation | 5 | bfs | 363,024 | 104 | 0 |
| S4 | Multi-region stale reroute | 5 | bfs | 150,533 | 18 | 0 |

All four faulty synthetic models expose harmful races. All four control models expose zero harmful races.

## Runtime and tested configurations

The reviewer smoke test was checked from a fresh clone on macOS with Colima and the RaceLoom Docker image running as `linux/amd64`.

| Test | Machine | Result | Bad/control RaceLoom time |
|---|---|---|---:|
| B2 Docker smoke test | macOS 26.5.1 / Apple M1 / Colima / `linux/amd64` | PASS | 15.824144s / 16.730201s |

The full B1--B4 matrix and S1--S4 synthetic benchmarks were validated on the following server.

| Item | Exact value |
|---|---|
| OS | Ubuntu 24.04.3 LTS |
| Kernel | 6.8.0-87-generic #88-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 09:28:41 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux |
| CPU model | Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz |
| CPUs reported by `lscpu` | 64 |
| CPUs available to the process from `nproc` | 64 |
| Memory | 135025090560 bytes = 125.751915 GiB = 135.025091 GB |

Total recorded runtimes:

| Benchmark set | Total recorded runtime |
|---|---:|
| B1--B4 main matrix | 36611.170621s = 610.186 min |
| S1--S4 synthetic set | 8254.524522s = 137.575 min |

Detailed runtime information is recorded in:

- `docs/runtime_summary.md`
- `docs/benchmark_runtimes_exact.tsv`
- `docs/tested_configurations.md`

## Running benchmarks

Run one benchmark pair:

```bash
bash scripts/docker_run_pair.sh benchmarks/smoke/b2_route_mapping_smoke/T1_atlanta 4 results/smoke_b2_route_mapping bfs
```

Run the default smoke test:

```bash
bash scripts/docker_smoke_test.sh
```

Run the full synthetic S1--S4 set:

```bash
bash benchmarks/synthetic/run_synthetic_s1_s4.sh
```

Full B1--B4 reruns are larger and should be run on native Linux/amd64 or a comparable server.

## Sources and scenario inspirations

The benchmark scenarios are RaceLoom model-level abstractions. They do not execute production SDN controllers directly. The source-derived families are inspired by safety concerns and mechanisms associated with the following systems and papers.

| Benchmark family | Source / inspiration |
|---|---|
| B1 waypoint / IDS-bypass | SIMPLE middlebox policy enforcement: https://dl.acm.org/doi/10.1145/2534169.2486022 |
| B2 wrong next-hop / route update | Ryu SDN framework: https://ryu-sdn.org/ |
| B3 slice isolation | FlowVisor network virtualization: https://yuba.stanford.edu/~nickm/papers/sigcomm09_flowvisor.pdf |
| B4 failover / stale path | FAUCET SDN controller and documentation: https://docs.faucet.nz/en/latest/intro.html |

## Topology sources

The selected topologies are used as concrete graph embeddings for the benchmark race patterns.

| Topology | Source |
|---|---|
| T1 Atlanta | SNDlib / TopoHub |
| T2 Nobel-EU | SNDlib / TopoHub |
| T3 Geant2012 | Internet Topology Zoo / TopoHub |
| T4 Germany50 | SNDlib / TopoHub |

Topology source links:

- SNDlib: https://sndlib.put.poznan.pl/
- Internet Topology Zoo: https://topology-zoo.org/
- TopoHub: https://www.topohub.org/

## Scope

These benchmarks are RaceLoom model-level artifacts. They are source-derived or synthetic abstractions of SDN race scenarios, not full executions of production SDN controllers. Symbolic ports in the models represent traffic classes, decision points, safe outcomes, and forbidden outcomes; they should not always be read as physical switch ports.

## License

This repository is licensed under the Creative Commons Attribution 4.0 International License (CC-BY-4.0). See `LICENSE`.

RaceLoom-Bench does not include RaceLoom itself. RaceLoom is distributed separately through its own artifact record and license. This repository contains benchmark models, properties, topology assets, helper scripts, result summaries, and sanitized validation logs.

## Citation

If you use this benchmark suite, please cite the RaceLoom paper/artifact and this repository. See `docs/references.md`.

## Reproducing paper numbers from validation logs

The repository includes sanitized validation logs for the runs used to report the benchmark numbers.

| Item | Path |
|---|---|
| Sanitized validation logs | `docs/validation_logs/` |
| Reproduction guide | `docs/reproduce_paper_numbers.md` |
| Extraction/checking script | `scripts/extract_paper_numbers_from_logs.py` |

To reproduce and check the reported trace counts and harmful-race counts from the logs, run:

```bash
python3 scripts/extract_paper_numbers_from_logs.py
```

The script parses 40 validation logs and checks the extracted numbers against the committed summary TSV files.
