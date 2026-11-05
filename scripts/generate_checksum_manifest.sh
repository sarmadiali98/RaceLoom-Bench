#!/usr/bin/env bash
set -euo pipefail

# Regenerate provenance/checksums.sha256 over the release-critical file set.
#
# Scope (keep in sync with the manifest header written below):
#   ARTIFACT.md, README.md, LICENSE, CITATION.cff, THIRD_PARTY_NOTICES.md,
#   RELEASE.md, REUSE.toml, LICENSES/ (all files), benchmarks/ (all files),
#   topology_assets/ (all files), scripts/*.sh, scripts/*.py,
#   scripts/README.md, tools/generators/*.py, docs/*.md, docs/*.tsv,
#   docs/validation_logs/ (all files), provenance/runtime.txt,
#   provenance/experiment_manifest.json.
#
# Excluded: this manifest itself (self-referential hashing is avoided),
# .git/, __pycache__/, results/ (untracked working evidence), and
# docs/REVIEWER_FIX_PROGRESS.md and docs/RELICO_COMPARISON.md (internal
# development-history documents, not release-critical), and other generated
# or git-ignored paths. CITATION.cff is release-critical: when its
# approval-pending fields are finalized, regenerate this manifest.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT"

OUT="provenance/checksums.sha256"

if command -v sha256sum >/dev/null 2>&1 && sha256sum /dev/null >/dev/null 2>&1; then
  SHA256_TOOL="sha256sum"
elif command -v shasum >/dev/null 2>&1 && shasum -a 256 /dev/null >/dev/null 2>&1; then
  SHA256_TOOL="shasum -a 256"
else
  printf 'ERROR: no SHA-256 utility available\n' >&2
  exit 1
fi

TMP_LIST="$(mktemp "${TMPDIR:-/tmp}/raceloom-checksum-paths.XXXXXX")"
TMP_OUT="$(mktemp "${TMPDIR:-/tmp}/raceloom-checksum-out.XXXXXX")"
trap 'rm -f "$TMP_LIST" "$TMP_OUT"' EXIT

{
  printf '%s\n' ARTIFACT.md README.md LICENSE CITATION.cff THIRD_PARTY_NOTICES.md RELEASE.md REUSE.toml
  find LICENSES benchmarks topology_assets -type f
  find scripts -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' -o -name '*.md' \)
  find tools/generators -maxdepth 1 -type f -name '*.py'
  find docs -maxdepth 1 -type f \( -name '*.md' -o -name '*.tsv' \)
  find docs/validation_logs -type f
  printf '%s\n' provenance/runtime.txt provenance/experiment_manifest.json
} | grep -v -e '^docs/REVIEWER_FIX_PROGRESS\.md$' -e '^docs/RELICO_COMPARISON\.md$' \
  | LC_ALL=C sort -u > "$TMP_LIST"

# Every listed path must exist; abort rather than emit a manifest with holes.
while IFS= read -r p; do
  [ -f "$p" ] || { printf 'ERROR: release-critical path missing: %s\n' "$p" >&2; exit 1; }
done < "$TMP_LIST"

{
  printf '# RaceLoom-Bench release-critical file checksums (SHA-256)\n'
  printf '# Format: <sha256>  <repo-relative-path>  (verify with: sha256sum -c provenance/checksums.sha256 or shasum -a 256 -c provenance/checksums.sha256)\n'
  printf '# Scope: ARTIFACT.md, README.md, LICENSE, CITATION.cff, THIRD_PARTY_NOTICES.md, RELEASE.md, REUSE.toml, LICENSES/, benchmarks/, topology_assets/, scripts/ (*.sh, *.py, *.md), tools/generators/ (*.py), docs/ (*.md, *.tsv, validation_logs/), provenance/runtime.txt, provenance/experiment_manifest.json\n'
  printf '# Excluded from this manifest: this file itself (self-referential hashing is avoided), .git/, __pycache__/, results/ (untracked working evidence), docs/REVIEWER_FIX_PROGRESS.md and docs/RELICO_COMPARISON.md (internal development-history documents, not release-critical), and other generated or git-ignored paths.\n'
  while IFS= read -r p; do
    case "$SHA256_TOOL" in
      sha256sum) sha256sum -- "$p" ;;
      "shasum -a 256") shasum -a 256 -- "$p" ;;
    esac
  done < "$TMP_LIST"
} > "$TMP_OUT"

mv -f "$TMP_OUT" "$OUT"
printf 'wrote %s (%s release-critical files)\n' "$OUT" "$(wc -l < "$TMP_LIST" | tr -d '[:space:]')"
