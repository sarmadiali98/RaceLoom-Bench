# RaceLoom-Bench release package

This directory is the RaceLoom-Bench v1.1.0 release package. Start at
[`ARTIFACT.md`](ARTIFACT.md) — it walks you from a clean machine to a
reproduced, independently validated result and assumes no prior knowledge of
the project.

## What is in this package

| Path | Contents |
|---|---|
| `ARTIFACT.md` | Reviewer entry point: obtain → install → verify → smoke → individual → full → validate. |
| `README.md` | Artifact overview, benchmark matrix, sources, license. |
| `LICENSE` | MIT license for the original RaceLoom-Bench material, with a scope statement excluding third-party material. |
| `THIRD_PARTY_NOTICES.md` | Authoritative component-by-component licensing record, attributions, and redistribution conditions. |
| `REUSE.toml` | Machine-readable file-to-license mapping (REUSE 3.3). |
| `LICENSES/` | License texts for the identifiers used in `REUSE.toml` (`MIT.txt`, `CC-BY-4.0.txt`, `LicenseRef-ZIB-Academic-License.txt`). |
| `CITATION.cff` | Citation metadata (version 1.1.0, author Ali Sarmadi, Tehran Institute for Advanced Studies; `date-released` is set to the actual publication date at Zenodo deposit time). |
| `RELEASE.md` | This file: package layout and archive checksums. |
| `benchmarks/` | Benchmark inputs: 16 principal B1–B4 configurations, 4 supplementary S1–S4 configurations, 5 auxiliary smoke configurations (models, properties, metadata, expected statistics). |
| `topology_assets/` | Derived topology asset JSON files, their source/attribution documentation, and the unmodified SNDlib license text (`licenses/SNDlib_ZIB_Academic_License.txt`). |
| `scripts/` | Canonical execution pipeline, environment verification, runtime setup, independent scientific checkers, and their test suites. |
| `tools/` | Topology-asset generators (`tools/generators/`): the committed, documented procedure that reconstructs the topology assets from publicly available TopoHub inputs — `make_raceloom_topology_asset.py` converts a TopoHub GraphML topology into a RaceLoom topology-asset JSON, and `make_b1_b2_geant2012_k14.py` regenerates the Geant2012 K14 benchmark embedding from the `T3_geant2012.json` asset. |
| `docs/` | Installation, reproduction, validation, and results documentation; sanitized historical validation logs; result matrices. |
| `provenance/` | Release checksum manifest (`checksums.sha256`), experiment manifest, runtime record. |
| `raceloom-bench-evidence.tar.gz` | Scientific evidence archive of the verified reference reproduction (2026-11-04): per-configuration evidence for all 20 baseline-backed configurations, both independent checkers' reports, the sanitized historical expectation logs, and auxiliary smoke evidence. |

Not included: the RaceLoom runtime (obtained separately from its official
Zenodo record — see `ARTIFACT.md` Step 3), internal development history, and
development-only tools.

## Integrity verification

Verify the release-critical files first (from this directory):

```bash
sha256sum -c provenance/checksums.sha256        # Linux
shasum -a 256 -c provenance/checksums.sha256    # macOS
```

Every line must end with `: OK`. The manifest covers every release-critical
file in this package except itself and the evidence archive, whose checksum is
recorded separately below (an archive cannot list its own checksum inside
itself).

## Archive checksums (distinct scopes)

| Archive | Role | SHA-256 | Size (bytes) |
|---|---|---|---|
| `raceloom-bench-evidence.tar.gz` (bundled here) | Scientific evidence of the verified reference reproduction | `7d2b73c1a860520385c6eaa04fc64d71df34c5994d489f4e0fb5f10412d97b99` | 3,735,486 |
| `raceloom.tar.gz` (external, Zenodo DOI 10.5281/zenodo.16884345) | RaceLoom runtime Docker image; downloaded and verified by `scripts/setup_raceloom_artifact.sh`, never bundled | `bc533c637a0fa55e51f6c84c07137bdd44ddbd303c9a2443ab6301710ec58d45` | 794,997,198 |

To verify the bundled evidence archive:

```bash
sha256sum raceloom-bench-evidence.tar.gz         # must print 7d2b73c1...d97b99
mkdir evidence && tar -xzf raceloom-bench-evidence.tar.gz -C evidence
cd evidence/raceloom-bench-evidence-build
sha256sum -c checksums.sha256        # Linux; shasum -a 256 -c checksums.sha256 on macOS
```

The evidence archive's internal checksum manifest covers every file it
contains. The two checker reports inside (`checker_reports/`) show the
verified reference results: 16/16 principal and 4/4 supplementary
`SCIENTIFIC_MATCH`. See `docs/RESULTS.md` and `docs/VALIDATION.md`.

The RaceLoom runtime archive is a third-party artifact: it is downloaded from
Zenodo, verified against the checksum above, loaded, and checked against the
pinned image ID `sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087`
before use. It is governed by the RaceLoom license (Apache-2.0), not by this
repository's MIT license — see `THIRD_PARTY_NOTICES.md`.

## Relationship to the original RaceLoom

RaceLoom-Bench is a benchmark suite *for* RaceLoom, a model checker for SDN
race conditions developed by Andrei-Ion Covaci (RaceLoom paper: Caltais,
Covaci, Hojjat, IFM 2025). RaceLoom-Bench does not include or modify RaceLoom:
it supplies benchmark inputs through read-only bind mounts and executes the
unmodified, checksum-pinned RaceLoom Docker image. The two artifacts are
distributed separately and are licensed separately (MIT for RaceLoom-Bench's
original material; Apache-2.0 for RaceLoom).

## Licensing status of this package

The package uses a multi-license structure, recorded authoritatively in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and machine-readably in
[`REUSE.toml`](REUSE.toml):

- Original RaceLoom-Bench material: **MIT** (`LICENSE` opens with a scope
  statement that excludes third-party material from the MIT grant).
- RaceLoom runtime: **Apache-2.0**, obtained separately, never bundled.
- Geant2012 derivative (`T3_geant2012.json` and its benchmark topology copy):
  **CC BY 4.0**, redistribution permitted with the included attribution.
- SNDlib derivatives (`T1_atlanta.json`, `T2_nobel_eu.json`,
  `T4_germany50.json` and their 17 benchmark topology copies): **ZIB Academic
  License** (unmodified text bundled at
  `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt` and in
  `LICENSES/LicenseRef-ZIB-Academic-License.txt`). The license governs these
  files as a separately licensed component; its conditions are stated in the
  bundled license text itself, and the documented regeneration procedure
  (`topology_assets/README.md`) reconstructs the assets from publicly
  available TopoHub inputs.

This licensing status does not affect the scientific contents of the package:
models, expected statistics, validation logs, and evidence are unchanged.

## Publication metadata guidance (Zenodo)

The proposed Zenodo record metadata should describe the multi-license
arrangement explicitly rather than labeling the entire archive with a single
license:

- **License field:** MIT — describing the original RaceLoom-Bench material,
  which constitutes the artifact itself.
- **Description field:** must state that certain third-party components are
  distributed under their own licenses — the SNDlib-derived topology files
  under the ZIB Academic License, the Geant2012 derivative under CC BY 4.0,
  and that the RaceLoom runtime is not part of the archive and is obtained
  separately under Apache-2.0 — and must point to `THIRD_PARTY_NOTICES.md`
  and `REUSE.toml` in the archive for the complete mapping.
- If Zenodo's single-license field cannot accurately represent this
  arrangement at publication time, the license field must not silently
  mislabel the third-party material; the description-field statement above is
  the required corrective, and the metadata should be checked against
  `THIRD_PARTY_NOTICES.md` before publication.
