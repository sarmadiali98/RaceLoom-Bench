# References

This benchmark repository is a companion artifact for RaceLoom.

## RaceLoom

- RaceLoom paper/artifact title: RaceLoom: a tool for automated symbolic detection of SDN race hazards
- RaceLoom artifact DOI: https://doi.org/10.5281/zenodo.16884345
- RaceLoom artifact download: https://zenodo.org/records/16884345/files/raceloom.tar.gz?download=1
- RaceLoom repository: https://github.com/andreioff/RaceLoom

## RaceLoom-Bench

- Repository: https://github.com/sarmadiali98/RaceLoom-Bench

This repository contains benchmark models, properties, topology assets, expected results, and helper scripts. It does not include RaceLoom itself. To run the benchmarks, first obtain the RaceLoom Docker artifact using `scripts/setup_raceloom_artifact.sh`.

## License note

This repository uses a multi-license structure: the MIT license applies to the original RaceLoom-Bench material only (see `LICENSE` and `THIRD_PARTY_NOTICES.md` for the exact scope). RaceLoom itself is not included in this repository and remains distributed separately through its own artifact record and its own license: RaceLoom is Apache-2.0 (copyright Andrei-Ion Covaci), obtained from the Zenodo artifact record above. Topology datasets retain their upstream terms: the Geant2012 derivative carries CC BY 4.0 (attribution required), and the Atlanta, Nobel-EU, and Germany50 derivatives are governed by the ZIB Academic License of SNDlib (unmodified license text: `topology_assets/licenses/SNDlib_ZIB_Academic_License.txt`). These upstream licenses govern their respective topology files as separately licensed components; `THIRD_PARTY_NOTICES.md` §4 summarizes the component-level arrangement and `REUSE.toml` provides the machine-readable file-to-license mapping.
