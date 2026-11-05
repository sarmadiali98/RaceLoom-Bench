# Topology assets

This directory contains JSON assets for the selected benchmark topologies.

| File | Topology | Source | Upstream license |
|---|---|---|---|
| `T1_atlanta.json` | Atlanta | SNDlib / TopoHub | ZIB Academic License (SNDlib); see `licenses/SNDlib_ZIB_Academic_License.txt` and `THIRD_PARTY_NOTICES.md` §4 |
| `T2_nobel_eu.json` | Nobel-EU | SNDlib / TopoHub | ZIB Academic License (SNDlib); see `licenses/SNDlib_ZIB_Academic_License.txt` and `THIRD_PARTY_NOTICES.md` §4 |
| `T3_geant2012.json` | Geant2012 | Internet Topology Zoo / TopoHub | CC BY 4.0 (attribution required) |
| `T4_germany50.json` | Germany50 | SNDlib / TopoHub | ZIB Academic License (SNDlib); see `licenses/SNDlib_ZIB_Academic_License.txt` and `THIRD_PARTY_NOTICES.md` §4 |
| `selected_topologies.json` | Metadata for the selected topology set | Repository metadata | MIT (this repository) |
| `licenses/SNDlib_ZIB_Academic_License.txt` | Unmodified license text served by SNDlib | https://sndlib.put.poznan.pl/LICENSE.txt | n/a (license text itself) |

These JSON files are **derived abstractions** of the upstream graphs (anonymized
node labels, node/edge lists only), produced by the committed generator
`tools/generators/make_raceloom_topology_asset.py`. The upstream licenses above
govern these derived files and the benchmark topology copies derived from them
(`source/topology.json` in each benchmark instance); the MIT license of this
repository applies to the original RaceLoom-Bench material and does not alter
the upstream terms. The machine-readable mapping is `REUSE.toml` at the
repository root.

## License conditions

- **Geant2012 (Internet Topology Zoo, CC BY 4.0):** redistribution is
  permitted with attribution — dataset DOI
  [10.25909/30153949](https://doi.org/10.25909/30153949); S. Knight, H. X. Nguyen,
  N. Falkner, R. Bowden, M. Roughan, "The Internet Topology Zoo", *IEEE Journal on
  Selected Areas in Communications*, 29(9):1765–1775, 2011; license
  https://creativecommons.org/licenses/by/4.0/; adaptation indicated here and in
  `THIRD_PARTY_NOTICES.md` §6.
- **SNDlib (Atlanta, Nobel-EU, Germany50, ZIB Academic License):** the license
  text is reproduced unmodified in
  [`licenses/SNDlib_ZIB_Academic_License.txt`](licenses/SNDlib_ZIB_Academic_License.txt)
  (retrieved from the official https://sndlib.put.poznan.pl/LICENSE.txt; an
  archived copy of that URL is available at
  https://web.archive.org/web/20240422030848/https://sndlib.put.poznan.pl/LICENSE.txt,
  and `sndlib.zib.de` redirects to the official site). The license governs the
  SNDlib-derived topology files as a separately licensed component; its
  conditions — academic-use eligibility, citation of the authors, preservation
  of the unmodified license text, and the redistribution conditions of its
  clause 3 — are stated in the license text itself, which is authoritative.
  See `THIRD_PARTY_NOTICES.md` §4 for the component-level summary and the
  regeneration procedure.
- **TopoHub (conversion source, MIT):** https://www.topohub.org/; P. Jurkiewicz,
  "TopoHub: A repository of reference Gabriel graph and real-world topologies for
  networking research", *SoftwareX*, 24:101540, 2023, DOI 10.1016/j.softx.2023.101540.
  The TopoHub MIT license covers the TopoHub repository as published; the upstream
  dataset terms above still govern the underlying network data.

## Regenerating the topology assets

The committed generator
[`tools/generators/make_raceloom_topology_asset.py`](../tools/generators/make_raceloom_topology_asset.py)
reconstructs every asset in this directory from publicly available TopoHub
GraphML inputs. You only need this if you want to regenerate the assets
yourself; the committed assets are complete and checksum-verified.

1. **Source data.** The inputs are the TopoHub conversions of the upstream
   datasets: SNDlib networks (`atlanta`, `nobel-eu`, `germany50`) from
   [TopoHub](https://www.topohub.org/)
   ([repository](https://github.com/piotrjurkiewicz/topohub), `sndlib/*`), and
   Geant2012 from TopoHub's `topozoo/*` (originally the Internet Topology Zoo).
   Place the GraphML inputs under `data/sndlib/*.graphml` (and the Geant2012
   input alongside them) in a working directory.

2. **Generator.** Each asset is produced by one invocation of the generator:

   ```bash
   python3 tools/generators/make_raceloom_topology_asset.py \
       data/sndlib/atlanta.graphml   T1_atlanta   sndlib/atlanta        topology_assets/T1_atlanta.json
   python3 tools/generators/make_raceloom_topology_asset.py \
       data/sndlib/nobel-eu.graphml  T2_nobel_eu  sndlib/nobel-eu       topology_assets/T2_nobel_eu.json
   python3 tools/generators/make_raceloom_topology_asset.py \
       data/sndlib/germany50.graphml T4_germany50 sndlib/germany50      topology_assets/T4_germany50.json
   python3 tools/generators/make_raceloom_topology_asset.py \
       data/sndlib/Geant2012.graphml T3_geant2012 topology-zoo/geant2012 topology_assets/T3_geant2012.json
   ```

   The generator requires `networkx` (`python3 -m pip install networkx`). It
   reads the GraphML graph, keeps the largest connected component, relabels
   nodes to `n001`-style identifiers (recording the mapping in
   `node_label_mapping`), and computes the statistics and default anchor path
   recorded in each asset.

3. **Where the results are used.** Each generated asset is committed here and
   copied byte-for-byte (T1/T2/T4: with exactly one additional trailing
   newline) into the `source/topology.json` of every benchmark instance that
   uses it — see `benchmarks/final/*/K*/T*/source/topology.json` and
   `benchmarks/smoke/*/T1_atlanta/source/topology.json`. The benchmark models
   embed the same graph structure; regenerating an asset therefore also pins
   the graph data behind those models.

Full licensing details: [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

Source links:

- SNDlib: https://sndlib.put.poznan.pl/ (license: https://sndlib.put.poznan.pl/LICENSE.txt)
- Internet Topology Zoo: https://topology-zoo.org/
- TopoHub: https://www.topohub.org/
