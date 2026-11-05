# Third-party notices and license scope

This file is the authoritative component-by-component licensing record of the
RaceLoom-Bench artifact. It states (1) what the repository's MIT license
covers, (2) the license, source, and attribution of every third-party
component, and (3) how each component is distributed — bundled here or
obtained separately. The repository `LICENSE` states the same scope in brief,
and `REUSE.toml` provides the machine-readable file-to-license mapping.

## 1. What the MIT license covers

The repository `LICENSE` (MIT License, "Copyright (c) 2026 Ali Sarmadi")
applies to the **original RaceLoom-Bench material**:

- benchmark models (`model.json`), forwarding properties (`properties.json`),
  metadata, expected statistics, embeddings, and run scripts in `benchmarks/`
  (final, synthetic, smoke);
- topology-selection metadata (`topology_assets/selected_topologies.json`) and
  documentation;
- all execution, verification, checking, and test scripts in `scripts/` and
  `tools/generators/`;
- all original documentation (`ARTIFACT.md`, `README.md`, `RELEASE.md`,
  `CITATION.cff`, `docs/`, benchmark READMEs, this file);
- the provenance records (`provenance/`).

The MIT license does **not** cover the third-party material listed below. In
particular, the derived topology files that encode upstream network data are
distributed under their upstream licenses, not under MIT:

- `topology_assets/T1_atlanta.json`, `T2_nobel_eu.json`, `T4_germany50.json`
  and the 17 benchmark topology copies derived from them — ZIB Academic
  License (§4);
- `topology_assets/T3_geant2012.json` and its benchmark topology copy —
  CC BY 4.0 (§6).

The repository contains no third-party source code: all models, scripts, and
documentation are original work.

## 2. Component/license matrix

| Component | Copyright holder / source | License | Repository paths | Distribution | Attribution required |
|---|---|---|---|---|---|
| RaceLoom-Bench original material | Ali Sarmadi | MIT | repository root, `benchmarks/`, `scripts/`, `tools/generators/`, `docs/`, `provenance/` (except the topology files listed below) | this is the artifact | MIT notice (`LICENSE`) |
| SNDlib-derived topology files (Atlanta, Nobel-EU, Germany50) | SNDlib — ZIB / atesio and Poznań University of Technology (Orlowski, Pióro, Tomaszewski, Wessäly) | ZIB Academic License | `topology_assets/T1_atlanta.json`, `T2_nobel_eu.json`, `T4_germany50.json`; 17 benchmark copies at `benchmarks/final/{b1,b2,b3,b4}/K{8,12,16}/T{1,T2,T4}*/source/topology.json` and `benchmarks/smoke/*/T1_atlanta/source/topology.json` (full list in `REUSE.toml`) | redistributed, with the unmodified license text at `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt` | SNDlib citation (§4.3) + unmodified license text |
| Geant2012-derived topology files | Internet Topology Zoo — Matthew Roughan, Hung Nguyen, Nickolas Falkner (University of Adelaide) | CC BY 4.0 | `topology_assets/T3_geant2012.json`; `benchmarks/final/b1_waypoint_order_churn/K14/T3_geant2012/source/topology.json` | redistributed | Knight et al. 2011 citation + CC BY 4.0 attribution + adaptation indication (§6) |
| RaceLoom software (execution engine) | Andrei-Ion Covaci | Apache-2.0 | not in this repository | obtained separately from the official artifact record, checksum-pinned | RaceLoom paper citation (Caltais, Covaci, Hojjat, IFM 2025) |
| RaceLoom Docker image `raceloom.tar.gz` | RaceLoom authors | Zenodo record metadata declares CC BY 4.0; deposited code LICENSE is Apache-2.0; bundled components carry their own licenses | not in this repository | obtained separately (Zenodo DOI [10.5281/zenodo.16884345](https://doi.org/10.5281/zenodo.16884345)) | record terms |
| TopoHub (conversion source) | Piotr Jurkiewicz | MIT | not redistributed (only the derived assets above are shipped) | external source | Jurkiewicz, *SoftwareX* 24:101540, 2023 (§5) |
| Benchmark family inspiration: SIMPLE, Ryu, FlowVisor, FAUCET | respective authors | respective licenses | none — no code, text, or data incorporated | citations only | citations in `README.md` (§7) |

The bundled third-party components inside the RaceLoom Docker image (KATch,
Debian base packages, OpenJDK, Graphviz, Python packages) are identified in
§3; they are not redistributed by this repository.

## 3. RaceLoom software and its Docker distribution

RaceLoom is **not included** in this repository and is **not redistributed**
by it. Reviewers obtain it from the official RaceLoom artifact record (see
`docs/INSTALLATION.md` and `ARTIFACT.md` Step 3); `scripts/setup_raceloom_artifact.sh`
downloads the archive, verifies its SHA-256 against the checksum recorded for
this release, and verifies the loaded image ID against the pinned reference
image before use.

- License: Apache-2.0 ("Copyright 2025 Andrei-Ion Covaci"); repository
  https://github.com/andreioff/RaceLoom; artifact record Zenodo DOI
  [10.5281/zenodo.16884345](https://doi.org/10.5281/zenodo.16884345)
  (open access, version 0.1, published 2025-08-16).
- Paper: "Concurrency Under Control: Systematic Analysis of SDN Races
  Hazards", Georgiana Caltais, Andrei Covaci, Hossein Hojjat, IFM 2025.
- Note on the record metadata: the Zenodo record's license field declares
  CC BY 4.0 for the deposit, while the deposited `LICENSE` file and the
  repository are Apache-2.0. This concerns the RaceLoom authors' record; this
  repository links to the record and follows its terms without redistributing
  it.
- The RaceLoom repository contains no `NOTICE` file.
- Image contents (`raceloom.tar.gz`, 794,997,198 bytes, SHA-256
  `bc533c637a0fa55e51f6c84c07137bdd44ddbd303c9a2443ab6301710ec58d45`, pinned
  image ID `sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087`,
  amd64): RaceLoom source and benchmarks (Apache-2.0, LICENSE copied into the
  image), the KATch jar (cornell-netlab/KATch, Apache-2.0), the Debian
  bookworm base `python:3.12.11-bookworm` (Debian package license texts
  in-image; CPython under the PSF License Version 2), OpenJDK 17 (GPLv2 with
  Classpath Exception, as packaged by Debian), Graphviz (EPL family, as
  packaged by Debian), and the Python packages `maude`, `pydantic`,
  `matplotlib`, `pandas` and test extras (individual upstream licenses; the
  `maude` package binds the GPL-licensed Maude rewriting system).

Because RaceLoom-Bench only links to the official record and pins its
checksum, this repository does not redistribute the image or its components
and does not restate their full license texts. Anyone who re-redistributes
the image itself must comply with the applicable terms above; bundled-component
compliance inside the image is the RaceLoom authors' responsibility as its
distributor.

## 4. SNDlib — Atlanta, Nobel-EU, Germany50

### 4.1 What the assets are

Three benchmark topologies are derived from SNDlib networks:

| Asset | Upstream network | Where the derived data appears |
|---|---|---|
| `T1_atlanta.json` | SNDlib `atlanta` (15 nodes, 22 edges) | `topology_assets/`, plus one instance copy per T1 benchmark (`source/topology.json`) |
| `T2_nobel_eu.json` | SNDlib `nobel-eu` (28 nodes, 41 edges) | as above, for T2 |
| `T4_germany50.json` | SNDlib `germany50` (50 nodes, 88 edges) | as above, for T4 |

The derivation chain is: SNDlib native network files → TopoHub conversions
(https://github.com/piotrjurkiewicz/topohub, `sndlib/*`) → GraphML →
`tools/generators/make_raceloom_topology_asset.py` → anonymized JSON
(node/edge lists, `n001`-style labels, a `node_label_mapping` back to the
upstream node identifiers, computed statistics and anchor paths). The
benchmark models (`model.json`) then encode the same graph structure as
switches and port-based links; the models themselves are original work, while
the topology files listed above carry the upstream license.

### 4.2 Applicable license

The applicable component-level license for the SNDlib-derived topology files
is the **ZIB Academic License**, as served by SNDlib itself for its data and
format definitions. The unmodified license text is reproduced in
[`topology_assets/licenses/SNDlib_ZIB_Academic_License.txt`](topology_assets/licenses/SNDlib_ZIB_Academic_License.txt).

The official SNDlib site serves the license at
https://sndlib.put.poznan.pl/LICENSE.txt (the site is intermittently
unreachable; `sndlib.zib.de` redirects to it). The bundled text was retrieved
from the Internet Archive snapshot of that exact official URL (capture of
2024-04-22,
https://web.archive.org/web/20240422030848/https://sndlib.put.poznan.pl/LICENSE.txt),
which remains available as an archived reference.

### 4.3 Attribution

- Source: SNDlib — Survivable Network Design Library,
  https://sndlib.put.poznan.pl/ (Poznań University of Technology, with
  ZIB / atesio).
- Publication: S. Orlowski, M. Pióro, A. Tomaszewski, R. Wessäly, "SNDlib 1.0
  — Survivable Network Design Library", *Networks* 55(3):276–286, 2010,
  DOI [10.1002/net.20371](https://doi.org/10.1002/net.20371).
- License text: bundled unmodified at
  `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt`.
- Adaptation notice: the committed JSON assets are derived abstractions of
  the upstream networks (anonymized labels, node/edge lists, largest connected
  component where applicable), produced by the committed generator
  `tools/generators/make_raceloom_topology_asset.py`; the benchmark models
  embed the same graph structure.
- Clause 2 of the license requires appropriate citation and acknowledgement of
  the authors in every publication based on work using the data — satisfied by
  the citations above and in `docs/references.md`.

### 4.4 License scope and interpretation

The ZIB Academic License governs the SNDlib-derived topology files listed
above as a separately licensed component of this artifact; it does not extend
to the remainder of the repository, whose original material is MIT-licensed,
and nothing in this artifact alters the license terms of any third-party
material. The license was written for software and speaks of a "Program";
SNDlib applies it to its data, and this artifact applies it in the same way to
the data derived from SNDlib networks. The license's own text — bundled
unmodified — is authoritative for its conditions (academic-use eligibility,
citation, preservation of the license text, and the redistribution conditions
of clause 3). Anyone redistributing these files should read the bundled
license text; this summary is informational and not a legal opinion.

### 4.5 Regeneration from public inputs

The committed generator
[`tools/generators/make_raceloom_topology_asset.py`](tools/generators/make_raceloom_topology_asset.py)
reconstructs the committed topology assets from publicly available TopoHub
GraphML inputs placed under `data/sndlib/*.graphml` (for T3, the TopoHub
`topozoo` GraphML input for Geant2012). TopoHub is publicly available at
https://www.topohub.org/ and https://github.com/piotrjurkiewicz/topohub, and
the upstream SNDlib networks are available from the official SNDlib site under
the ZIB Academic License. The regeneration procedure is documented in
[`topology_assets/README.md`](topology_assets/README.md); it lists the exact
generator invocations for all four assets and where the resulting files are
used in the benchmarks. This keeps the preferred form of the derived data
available: reviewers can obtain the public inputs and regenerate the assets
with the committed generator instead of relying on the bundled files.

## 5. TopoHub (conversion source)

- TopoHub, https://www.topohub.org/ — repository
  https://github.com/piotrjurkiewicz/topohub, MIT License
  ("Copyright (c) 2023-2026 Piotr Jurkiewicz").
- Citation: P. Jurkiewicz, "TopoHub: A repository of reference Gabriel graph
  and real-world topologies for networking research", *SoftwareX* 24:101540,
  2023, DOI [10.1016/j.softx.2023.101540](https://doi.org/10.1016/j.softx.2023.101540).
- Scope note: the MIT license covers the TopoHub repository/package as
  published. Its `sndlib/*` and `topozoo/*` data files are conversions of the
  upstream datasets above; the MIT license of TopoHub does not supersede the
  upstream dataset terms, which is why the SNDlib-derived files remain under
  the ZIB Academic License (§4) and the Geant2012 derivative under CC BY 4.0
  (§6). TopoHub code itself is not redistributed by this artifact.

## 6. Internet Topology Zoo — Geant2012 (CC BY 4.0)

- Data: Internet Topology Zoo, dataset Geant2012 (`Geant2012.gml`),
  https://topology-zoo.org/ — long-term mirror
  https://github.com/mroughan/InternetTopologyZoo (`gml/Geant2012.gml`,
  LICENSE file is the CC BY 4.0 legal code), figshare DOI
  [10.25909/30153949](https://doi.org/10.25909/30153949) (license field
  "CC BY 4.0").
- Publication: S. Knight, H. X. Nguyen, N. Falkner, R. Bowden, M. Roughan,
  "The Internet Topology Zoo", *IEEE Journal on Selected Areas in
  Communications*, vol. 29, no. 9, pp. 1765–1775, October 2011,
  DOI [10.1109/JSAC.2011.111002](https://doi.org/10.1109/JSAC.2011.111002).
- License: Creative Commons Attribution 4.0 International
  (https://creativecommons.org/licenses/by/4.0/).
- Redistribution: permitted with attribution. The required attribution is
  provided here and in `topology_assets/README.md`: the dataset citation
  above, the license link, and the indication that
  `topology_assets/T3_geant2012.json` is an adapted abstraction of the
  upstream graph (largest connected component, anonymized node labels,
  node/edge lists only; produced by the committed generator). The benchmark
  instance for T3 embeds the same graph structure.

## 7. Benchmark family inspiration (citations only)

The benchmark families cite the following systems and papers as conceptual
inspiration (`README.md`, "Source systems and papers"); no code, text, or data
from them is included in this repository:

- B1 waypoint / IDS-bypass — SIMPLE middlebox policy enforcement
  (https://dl.acm.org/doi/10.1145/2534169.2486022).
- B2 wrong next-hop / route update — Ryu SDN framework (https://ryu-sdn.org/).
- B3 slice isolation — FlowVisor network virtualization
  (https://yuba.stanford.edu/~nickm/papers/sigcomm09_flowvisor.pdf).
- B4 failover / stale path — FAUCET SDN controller
  (https://docs.faucet.nz/en/latest/intro.html).

## 8. Summary for redistributors

If you redistribute RaceLoom-Bench:

1. Keep the MIT `LICENSE` (including its scope statement) for the original
   RaceLoom-Bench material.
2. Keep this notices file, `REUSE.toml`, and
   `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt` with the
   distribution.
3. Do not describe the combined artifact (RaceLoom-Bench + RaceLoom runtime)
   as entirely MIT-licensed: the runtime is Apache-2.0 and obtained
   separately, the SNDlib-derived topology material carries the ZIB Academic
   License, and the Geant2012 derivative carries CC BY 4.0.
4. Redistribution of the SNDlib-derived topology files is subject to the ZIB
   Academic License; read the bundled license text before re-distributing
   them. The documented regeneration path (§4.5) is an alternative for
   obtaining the derived data from public inputs.
5. If you also redistribute the RaceLoom Docker image, comply with Apache-2.0
   for the RaceLoom code and respect the Zenodo record's terms.
6. Preserve the dataset attributions in this file and in
   `topology_assets/README.md`.
