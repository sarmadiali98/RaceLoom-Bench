# Tested configurations

This file records the exact systems used for benchmark validation and smoke-test checks.

## Full benchmark validation server

| Item | Exact value |
|---|---|
| OS | Ubuntu 24.04.3 LTS |
| Kernel | 6.8.0-87-generic #88-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 09:28:41 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux |
| CPU model | Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz |
| CPUs reported by `lscpu` | 64 |
| CPUs reported by `nproc --all` | 128 |
| CPUs available to the process from `nproc` | 64 |
| Memory | 135025090560 bytes = 125.751915 GiB = 135.025091 GB |
| Python | 3.13.5 |
| Java | OpenJDK 1.8.0_492 |
| RaceLoom `main.py` SHA-256 | `c77059168460593a2980f23398b73cc3dd68e646466fb380371e83bce515f120` |

The full validation results are summarized in:

- `docs/final_4x4_matrix.md`
- `docs/synthetic_s1_s4_matrix.md`
- `docs/runtime_summary.md`
- `docs/benchmark_runtimes_exact.tsv`

## Reviewer smoke-test system

| Item | Exact value |
|---|---|
| Host OS | macOS 26.5.1, build 25F80 |
| Kernel | Darwin MacBook-Air-3.local 25.5.0 Darwin Kernel Version 25.5.0: Mon Apr 27 20:38:00 PDT 2026; root:xnu-12377.121.6~2/RELEASE_ARM64_T8103 arm64 |
| CPU | Apple M1 |
| Physical CPUs reported by macOS | 8 |
| Logical CPUs reported by macOS | 8 |
| Host memory | 8589934592 bytes = 8.000000 GiB |
| Docker client version | 29.4.3 |
| Docker server version | 29.2.1 |
| Docker server OS/architecture | linux/aarch64 |
| Docker VM operating system | Ubuntu 24.04.4 LTS |
| Docker VM CPUs | 4 |
| Docker VM memory | 8307826688 bytes |
| RaceLoom image ID | `sha256:8c16a50fd72f464170dab459fe513120bfaaa5dad7efb764b34f5bc1b5015908` |
| RaceLoom image tags | `["raceloom:latest"]` |
| RaceLoom image OS/architecture | linux/amd64 |
| RaceLoom image size | 1992659308 bytes |
| Container platform used | `linux/amd64` |
| RaceLoom workdir | `/raceloom` |
| RaceLoom command | `python main.py` |

Smoke-test result:

| Side | Branches | Traces | Harmful races | Total execution time |
|---|---|---:|---:|---:|
| bad | `CRoute:1;BSw:2` | 8 | 1 | 15.824144s |
| control | `CRoute:1;BSw:2` | 8 | 0 | 16.730201s |

Apple Silicon uses amd64 emulation for this image, so the smoke-test runtime is a compatibility reference rather than a native Linux/amd64 performance measurement.
