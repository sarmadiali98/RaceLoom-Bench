#!/usr/bin/env python3
"""Independent, read-only scientific result checker for the RaceLoom-Bench final 4x4 matrix.

Compares newly generated matrix evidence (console logs, side-root final_stats.csv
files, completion markers, status.tsv records and per-configuration provenance)
against the historical expectations recorded in docs/final_4x4_matrix.tsv and
docs/validation_logs/main/. The checker never executes RaceLoom or Docker, never
modifies any input or evidence file, and uses the Python 3 standard library only.

Branch signatures ("Name:count;Name:count;...") are compared as order-independent
branch-name/count mappings rather than raw strings: the historical matrix TSV and
the RaceLoom runtime may emit the same branch counts in different orders. The
original signature strings are preserved in reports; malformed signatures and
duplicate branch names are rejected and can never produce a match.

Usage:
    python3 scripts/check_final_matrix.py --matrix-root /path/to/matrix-root
    python3 scripts/check_final_matrix.py --matrix-root ROOT --json
    python3 scripts/check_final_matrix.py --matrix-root ROOT --output report.json

Exit codes:
    0  all 16 configurations are SCIENTIFIC_MATCH
    1  validation unsuccessful (any other classification)
    2  environment or usage error (missing expectation sources, malformed
       matrix TSV, unreadable matrix root, ...)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "raceloom-matrix-check-report-v1"
EXPECTED_CONFIG_COUNT = 16
EXPECTED_STRATEGY = "bfs"

MATRIX_TSV_RELATIVE = Path("docs") / "final_4x4_matrix.tsv"
HISTORICAL_LOGS_RELATIVE = Path("docs") / "validation_logs" / "main"
BENCHMARKS_FINAL_RELATIVE = Path("benchmarks") / "final"

STATUS_TSV_NAME = "status.tsv"
PROVENANCE_NAME = "provenance.tsv"
COMPLETE_MARKER = "STATUS_COMPLETE"
IN_PROGRESS_MARKER = "STATUS_IN_PROGRESS"

STATUS_HEADER = [
    "config_id", "benchmark", "depth", "status", "exit_code",
    "utc_start", "utc_end", "evidence_dir", "detail",
]
STATUS_VALUES = {"COMPLETE", "FAILED", "BLOCKED", "SKIPPED_ALREADY_COMPLETE"}
OPERATIONAL_SUCCESS_STATUSES = {"COMPLETE", "SKIPPED_ALREADY_COMPLETE"}

PROVENANCE_SCHEMA = "raceloom-matrix-provenance-v1"

MATRIX_TSV_COLUMNS = [
    "benchmark", "topology", "k", "depth", "branches", "traces",
    "bad_harmful", "control_harmful",
]

FINAL_STATS_COLUMNS = [
    "date", "sdnModelFile", "forwardingPropsFilePath", "strategy", "depth",
    "modelBranchCounts", "tracesGenTime", "maudeExecTime",
    "traceGenCacheHits", "traceGenCacheMisses", "generatedTraces",
    "katchExecTime", "katchCacheHits", "katchCacheMisses", "harmfulRaces",
    "traceAnalyzerExecTime", "totalExecTime",
]
FINAL_STATS_INT_COLUMNS = [
    "depth", "traceGenCacheHits", "traceGenCacheMisses", "generatedTraces",
    "katchCacheHits", "katchCacheMisses", "harmfulRaces",
]
FINAL_STATS_TIMING_COLUMNS = [
    "tracesGenTime", "maudeExecTime", "katchExecTime",
    "traceAnalyzerExecTime", "totalExecTime",
]

SIDES = ("bad", "control")

CONSOLE_FIELD_KEYS = {
    "strategy": "Trace generation strategy",
    "depth": "Depth",
    "branches": "Network model branches",
    "gen_cache_hits": "Trace generation cache hits",
    "gen_cache_misses": "Trace generation cache misses",
    "traces": "Generated traces",
    "katch_cache_hits": "KATch total cache hits",
    "katch_cache_misses": "KATch total cache misses",
    "harmful": "Harmful races found",
}
CONSOLE_TIMING_KEYS = {
    "traces_gen_time": "Trace(s) generation time",
    "maude_exec_time": "Maude execution time",
    "katch_exec_time": "KATch total execution time",
    "analyzer_exec_time": "Trace Analyzer execution time",
    "total_exec_time": "Total execution time",
}
REQUIRED_CONSOLE_SCIENCE = [
    "strategy", "depth", "branches", "traces", "harmful",
    "gen_cache_hits", "gen_cache_misses", "katch_cache_hits", "katch_cache_misses",
]

CSV_TO_SCIENCE = {
    "strategy": "strategy",
    "depth": "depth",
    "modelBranchCounts": "branches",
    "traceGenCacheHits": "gen_cache_hits",
    "traceGenCacheMisses": "gen_cache_misses",
    "generatedTraces": "traces",
    "katchCacheHits": "katch_cache_hits",
    "katchCacheMisses": "katch_cache_misses",
    "harmfulRaces": "harmful",
}

REQUIRED_PROVENANCE_KEYS = [
    "provenance_schema", "config_id", "benchmark", "depth", "strategy",
    "execution_order", "bad_model_path", "bad_properties_path",
    "control_model_path", "control_properties_path",
    "sha256_bad_model", "sha256_bad_properties", "sha256_control_model",
    "sha256_control_properties", "sha256_tool", "requested_image",
    "resolved_image_id", "sha256_run_one_pair_sh",
    "sha256_run_raceloom_progress_sh", "sha256_run_final_matrix_sh",
    "git_branch", "git_head", "git_worktree_state", "wt_fingerprint",
    "pair_runner_arg_bench", "pair_runner_arg_depth",
    "pair_runner_arg_out_dir", "pair_runner_env_RACELOOM_OUTPUT_DIR",
    "console_dir", "artifacts_base_dir", "utc_prepared",
]
OPTIONAL_PROVENANCE_KEYS = [
    "image_architecture", "image_repo_digest",
    "note_sha256_run_final_matrix_sh", "wt_fingerprint_algorithm",
    "wt_fingerprint_utc", "wt_tracked_files",
    "wt_untracked_nonignored_files", "pair_runner_command",
    "utc_prepared_note", "host_hostname", "host_architecture",
    "docker_client_version", "docker_server_version",
    "host_python3_version", "runtime_python_version",
    "runtime_python_version_note",
]

PROVENANCE_SCRIPT_FILES = {
    "sha256_run_one_pair_sh": "scripts/run_one_pair.sh",
    "sha256_run_raceloom_progress_sh": "scripts/run_raceloom_progress.sh",
    "sha256_run_final_matrix_sh": "scripts/run_final_matrix.sh",
}

FAMILY_TAG_RE = re.compile(r"^B\d+$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
BRANCH_PART_RE = re.compile(r"^(?P<name>[^:;\s]+):(?P<count>[0-9]+)$")
FINAL_STATS_OPEN_RE = re.compile(r"^=+\s*Final\s+Stats\s*=+$")
FINAL_STATS_CLOSE_RE = re.compile(r"^=+$")
FIELD_LINE_RE = re.compile(r"^([^:]+):\s*(.*)$")

SCIENTIFIC_MATCH = "SCIENTIFIC_MATCH"
SCIENTIFIC_MISMATCH = "SCIENTIFIC_MISMATCH"
INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
NOT_RUN = "NOT_RUN"
PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"

CLASSIFICATION_PRECEDENCE = {
    INFRASTRUCTURE_FAILURE: 0,
    INCOMPLETE_EVIDENCE: 1,
    PROVENANCE_MISMATCH: 2,
    SCIENTIFIC_MISMATCH: 3,
    NOT_RUN: 4,
    SCIENTIFIC_MATCH: 5,
}

ALL_CLASSIFICATIONS = (
    SCIENTIFIC_MATCH,
    SCIENTIFIC_MISMATCH,
    INFRASTRUCTURE_FAILURE,
    INCOMPLETE_EVIDENCE,
    NOT_RUN,
    PROVENANCE_MISMATCH,
)

TIMING_POLICY = (
    "execution timing fields (generation, Maude, KATch, analyzer, total) are "
    "recorded as measurements only and never produce scientific mismatches"
)


class ExpectationError(Exception):
    pass


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def typed_int(raw):
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return None


def parse_kv_text(text):
    values = {}
    issues = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        if "=" not in line:
            issues.append(f"line {lineno}: not a key=value record: {line[:80]!r}")
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            issues.append(f"line {lineno}: empty key")
            continue
        if key in values:
            issues.append(f"line {lineno}: duplicate key {key!r}")
        values[key] = value
    return values, issues


def extract_final_stats_block(text):
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if FINAL_STATS_OPEN_RE.match(ln.strip())]
    if not starts:
        return None, False
    start = starts[-1]
    body = []
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if FINAL_STATS_CLOSE_RE.match(stripped):
            return body, True
        body.append(lines[j])
    return body, False


def parse_stats_fields(block_lines):
    fields = {}
    for line in block_lines:
        match = FIELD_LINE_RE.match(line.strip())
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def parse_branch_signature(signature):
    """Parse a branch signature such as 'CBg:14;CIngress:1' into a mapping.

    Returns (mapping, error). On success mapping is {branch_name: int_count}
    and error is None. Comparison via the mapping is order-independent: the
    historical matrix TSV and the RaceLoom runtime may list identical branch
    counts in different orders. Malformed signatures (empty, missing or
    non-integer counts, embedded whitespace, trailing separators) and duplicate
    branch names are rejected with a short human-readable error reason.
    """
    if signature is None:
        return None, "signature is missing"
    text = signature.strip()
    if not text:
        return None, "signature is empty"
    mapping = {}
    for index, part in enumerate(text.split(";"), 1):
        match = BRANCH_PART_RE.match(part)
        if not match:
            return None, (
                f"part {index} is not NAME:COUNT with a non-empty branch name "
                f"and a non-negative integer count: {part!r}"
            )
        name = match.group("name")
        if name in mapping:
            return None, f"duplicate branch name {name!r}"
        mapping[name] = int(match.group("count"))
    return mapping, None


def branch_signature_comparison(side, expected_raw, actual_raw, add):
    """Compare one branch signature against expectations, order-independently.

    Builds the branches comparison record for a side. The raw expected and
    actual signature strings are always preserved in the record; parsed
    name/count mappings are attached when both sides parse. Malformed or
    duplicate-laden signatures on either side are rejected as scientific
    mismatches and can never produce a match.
    """
    comparison = {
        "field": "branches",
        "expected": expected_raw,
        "actual": actual_raw,
        "outcome": None,
        "source": "matrix_tsv",
        "comparison": "order-independent branch-name/count mappings",
    }
    if actual_raw is None:
        comparison["outcome"] = "unavailable"
        return comparison
    expected_map, expected_error = parse_branch_signature(expected_raw)
    actual_map, actual_error = parse_branch_signature(actual_raw)
    if expected_map is not None:
        comparison["expected_branch_counts"] = expected_map
    if actual_map is not None:
        comparison["actual_branch_counts"] = actual_map
    if expected_error is not None:
        comparison["outcome"] = "malformed_expected"
        comparison["detail"] = expected_error
        add(SCIENTIFIC_MISMATCH, (
            f"{side}: branches expected signature is malformed ({expected_error}): "
            f"{expected_raw!r} (matrix TSV)"
        ))
        return comparison
    if actual_error is not None:
        comparison["outcome"] = "malformed_actual"
        comparison["detail"] = actual_error
        add(SCIENTIFIC_MISMATCH, (
            f"{side}: branches actual signature is malformed ({actual_error}): "
            f"{actual_raw!r}"
        ))
        return comparison
    if expected_map == actual_map:
        comparison["outcome"] = "match"
        return comparison
    only_expected = [name for name in expected_map if name not in actual_map]
    only_actual = [name for name in actual_map if name not in expected_map]
    differing = [
        name for name in expected_map
        if name in actual_map and expected_map[name] != actual_map[name]
    ]
    details = []
    if only_expected:
        details.append(f"branch names only in expected: {only_expected}")
    if only_actual:
        details.append(f"branch names only in actual: {only_actual}")
    if differing:
        details.append(
            "differing counts: "
            + ", ".join(
                f"{name} expected {expected_map[name]} actual {actual_map[name]}"
                for name in differing
            )
        )
    detail_text = "; ".join(details)
    comparison["outcome"] = "mismatch"
    comparison["detail"] = detail_text
    add(SCIENTIFIC_MISMATCH, (
        f"{side}: branches expected {expected_raw!r} (matrix TSV), actual {actual_raw!r} "
        f"({detail_text})"
    ))
    return comparison


def parse_console_log(path):
    issues = []
    text = read_text(path)
    block, terminated = extract_final_stats_block(text)
    if block is None:
        issues.append("no 'Final Stats' block found in console log")
        return {"science": {}, "timings": {}, "identity": {}, "output_written": False}, issues
    if not terminated:
        issues.append("'Final Stats' block is not terminated (truncated console log?)")
    fields = parse_stats_fields(block)
    science = {}
    for key, label in CONSOLE_FIELD_KEYS.items():
        if label in fields:
            science[key] = fields[label] if key in ("strategy", "branches") else typed_int(fields[label])
    timings = {key: fields[label] for key, label in CONSOLE_TIMING_KEYS.items() if label in fields}
    identity = {label: fields[label] for label in ("Date", "SDN model file", "Forwarding properties file") if label in fields}
    parsed = {
        "science": science,
        "timings": timings,
        "identity": identity,
        "output_written": "Output written to:" in text,
    }
    return parsed, issues


def parse_final_stats_csv(path):
    issues = []
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            rows = list(csv.reader(fh))
    except OSError as exc:
        return None, [f"cannot read final_stats.csv: {exc}"]
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return None, ["final_stats.csv has no content"]
    header = rows[0]
    if header != FINAL_STATS_COLUMNS:
        issues.append(
            "final_stats.csv header does not match the expected 17-column schema: "
            f"{header!r}"
        )
        return None, issues
    data = rows[1:]
    if len(data) != 1:
        issues.append(f"final_stats.csv must contain exactly one data row, found {len(data)}")
        return None, issues
    row = data[0]
    if len(row) != len(FINAL_STATS_COLUMNS):
        issues.append(
            f"final_stats.csv data row has {len(row)} fields, expected {len(FINAL_STATS_COLUMNS)}"
        )
        return None, issues
    raw = dict(zip(FINAL_STATS_COLUMNS, row))
    science = {}
    for column, key in CSV_TO_SCIENCE.items():
        value = raw[column].strip()
        if key in ("strategy", "branches"):
            science[key] = value
        else:
            science[key] = typed_int(value)
            if science[key] is None:
                issues.append(f"final_stats.csv column {column} is not a valid integer: {raw[column]!r}")
    timings = {column: raw[column].strip() for column in FINAL_STATS_TIMING_COLUMNS}
    identity = {
        "date": raw["date"],
        "sdnModelFile": raw["sdnModelFile"],
        "forwardingPropsFilePath": raw["forwardingPropsFilePath"],
    }
    return {"science": science, "timings": timings, "identity": identity}, issues


def parse_status_tsv(path):
    records = []
    issues = []
    text = read_text(path)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return records, ["status.tsv is empty"], False
    header = lines[0].split("\t")
    if header != STATUS_HEADER:
        return records, [
            "status.tsv header does not match the expected 9-column schema: "
            f"{header!r}"
        ], False
    for lineno, line in enumerate(lines[1:], 2):
        parts = line.split("\t")
        if len(parts) != len(STATUS_HEADER):
            issues.append(
                f"status.tsv line {lineno}: expected {len(STATUS_HEADER)} "
                f"tab-separated fields, found {len(parts)}"
            )
            continue
        records.append(dict(zip(STATUS_HEADER, parts)))
    return records, issues, True


def load_matrix_tsv(repo_root):
    path = repo_root / MATRIX_TSV_RELATIVE
    if not path.is_file():
        raise ExpectationError(f"matrix TSV not found: {path}")
    text = read_text(path)
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ExpectationError(f"matrix TSV has no data rows: {path}")
    header = lines[0].split("\t")
    if header != MATRIX_TSV_COLUMNS:
        raise ExpectationError(
            f"matrix TSV header does not match the expected schema "
            f"{MATRIX_TSV_COLUMNS!r}: {header!r}"
        )
    expectations = {}
    order = []
    for lineno, line in enumerate(lines[1:], 2):
        parts = line.split("\t")
        if len(parts) != len(MATRIX_TSV_COLUMNS):
            raise ExpectationError(
                f"matrix TSV line {lineno}: expected {len(MATRIX_TSV_COLUMNS)} "
                f"tab-separated fields, found {len(parts)}"
            )
        row = dict(zip(MATRIX_TSV_COLUMNS, parts))
        family_tag = row["benchmark"].split("_", 1)[0]
        if not FAMILY_TAG_RE.match(family_tag):
            raise ExpectationError(
                f"matrix TSV line {lineno}: benchmark {row['benchmark']!r} "
                "does not start with a B<n> family tag"
            )
        for column in ("depth", "traces", "bad_harmful", "control_harmful"):
            if not row[column].strip().isdigit():
                raise ExpectationError(
                    f"matrix TSV line {lineno}: column {column} is not a "
                    f"non-negative integer: {row[column]!r}"
                )
        config_id = f"{family_tag}_{row['k']}_{row['topology']}"
        if config_id in expectations:
            raise ExpectationError(
                f"matrix TSV line {lineno}: duplicate configuration {config_id}"
            )
        expectations[config_id] = {
            "config_id": config_id,
            "family_tag": family_tag,
            "benchmark_tsv": row["benchmark"],
            "topology": row["topology"],
            "k": row["k"],
            "depth": int(row["depth"]),
            "branches": row["branches"],
            "traces": int(row["traces"]),
            "bad_harmful": int(row["bad_harmful"]),
            "control_harmful": int(row["control_harmful"]),
            "tsv_line": lineno,
        }
        order.append(config_id)
    if len(expectations) != EXPECTED_CONFIG_COUNT:
        raise ExpectationError(
            f"matrix TSV must describe exactly {EXPECTED_CONFIG_COUNT} "
            f"configurations, found {len(expectations)}"
        )
    return expectations, order


def resolve_benchmark_dirs(repo_root, expectations):
    base = repo_root / BENCHMARKS_FINAL_RELATIVE
    if not base.is_dir():
        raise ExpectationError(f"benchmark root not found: {base}")
    needed_tags = {exp["family_tag"] for exp in expectations.values()}
    matches = {tag: [] for tag in needed_tags}
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        tag = entry.name.split("_", 1)[0].upper()
        if tag in matches:
            matches[tag].append(entry.name)
    resolved = {}
    for tag, names in sorted(matches.items()):
        if len(names) != 1:
            raise ExpectationError(
                f"benchmark family {tag}: expected exactly one directory under "
                f"{BENCHMARKS_FINAL_RELATIVE.as_posix()}, found {names!r}"
            )
        resolved[tag] = names[0]
    for config_id, exp in expectations.items():
        benchmark_dir = (
            f"{BENCHMARKS_FINAL_RELATIVE.as_posix()}/"
            f"{resolved[exp['family_tag']]}/{exp['k']}/{exp['topology']}"
        )
        exp["benchmark_dir"] = benchmark_dir
        exp["log_base"] = benchmark_dir.replace("/", "_")
    return resolved


def load_historical_log(repo_root, config_id, side):
    path = repo_root / HISTORICAL_LOGS_RELATIVE / f"{config_id}_{side}.txt"
    if not path.is_file():
        return None
    text = read_text(path)
    header = {}
    in_header = True
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("-----"):
            in_header = False
            continue
        if in_header and "=" in line:
            key, _, value = line.partition("=")
            header[key.strip()] = value.strip()
    block, _terminated = extract_final_stats_block(text)
    fields = parse_stats_fields(block) if block is not None else {}
    cache = {}
    for key, label in (
        ("gen_cache_hits", "Trace generation cache hits"),
        ("gen_cache_misses", "Trace generation cache misses"),
        ("katch_cache_hits", "KATch total cache hits"),
        ("katch_cache_misses", "KATch total cache misses"),
    ):
        value = typed_int(fields.get(label))
        if value is not None:
            cache[key] = value
    return {
        "path": path,
        "header": header,
        "cache": cache,
        "traces": typed_int(fields.get("Generated traces")),
        "harmful": typed_int(fields.get("Harmful races found")),
        "branches": fields.get("Network model branches"),
        "depth": typed_int(fields.get("Depth")),
        "strategy": fields.get("Trace generation strategy"),
    }


def read_git_head(repo_root):
    git_dir = repo_root / ".git"
    try:
        if git_dir.is_file():
            content = git_dir.read_text(encoding="utf-8", errors="replace").strip()
            if content.startswith("gitdir:"):
                git_dir = Path(content.split(":", 1)[1].strip())
                if not git_dir.is_absolute():
                    git_dir = repo_root / git_dir
            else:
                return None
        if not git_dir.is_dir():
            return None
        head_path = git_dir / "HEAD"
        if not head_path.is_file():
            return None
        head = head_path.read_text(encoding="utf-8", errors="replace").strip()
        if head.startswith("ref:"):
            ref = head.split(":", 1)[1].strip()
            ref_path = git_dir / ref
            if ref_path.is_file():
                value = ref_path.read_text(encoding="utf-8", errors="replace").strip()
                return value or None
            packed = git_dir / "packed-refs"
            if packed.is_file():
                for raw in packed.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or line.startswith("^"):
                        continue
                    sha, _, ref_name = line.partition(" ")
                    if ref_name == ref:
                        return sha
            return None
        if SHA1_RE.match(head):
            return head
        return None
    except OSError:
        return None


def count_files(directory):
    if not directory.is_dir():
        return 0
    return sum(1 for entry in directory.iterdir() if entry.is_file())


def evaluate_provenance(exp, repo_root, values, checks, add, warnings):
    cfg_id = exp["config_id"]
    missing = [
        key for key in REQUIRED_PROVENANCE_KEYS
        if key not in values or not values[key].strip()
    ]
    if missing:
        add(INCOMPLETE_EVIDENCE, f"provenance record is missing required fields: {', '.join(missing)}")
    optional_missing = [key for key in OPTIONAL_PROVENANCE_KEYS if key not in values]
    if optional_missing:
        warnings.append(f"provenance record lacks optional fields: {', '.join(optional_missing)}")

    if values.get("provenance_schema") not in (None, PROVENANCE_SCHEMA):
        add(PROVENANCE_MISMATCH, f"provenance provenance_schema={values.get('provenance_schema')!r} does not match {PROVENANCE_SCHEMA!r}")
    if values.get("config_id") not in (None, cfg_id):
        add(PROVENANCE_MISMATCH, f"provenance config_id={values.get('config_id')!r} does not match configuration {cfg_id!r}")
    if values.get("benchmark") not in (None, exp["benchmark_dir"]):
        add(PROVENANCE_MISMATCH, f"provenance benchmark={values.get('benchmark')!r} does not match {exp['benchmark_dir']!r}")
    if values.get("depth") not in (None, str(exp["depth"])):
        add(PROVENANCE_MISMATCH, f"provenance depth={values.get('depth')!r} does not match expected depth {exp['depth']}")
    if values.get("strategy") not in (None, EXPECTED_STRATEGY):
        add(PROVENANCE_MISMATCH, f"provenance strategy={values.get('strategy')!r} does not match expected strategy {EXPECTED_STRATEGY!r}")
    if values.get("execution_order") not in (None, "bad_then_control"):
        add(PROVENANCE_MISMATCH, f"provenance execution_order={values.get('execution_order')!r} is unexpected")

    input_map = [
        ("sha256_bad_model", "bad", "model.json"),
        ("sha256_bad_properties", "bad", "properties.json"),
        ("sha256_control_model", "control", "model.json"),
        ("sha256_control_properties", "control", "properties.json"),
    ]
    for key, side, name in input_map:
        recorded = values.get(key)
        relative = f"{exp['benchmark_dir']}/{side}/{name}"
        repo_file = repo_root / relative
        check = {"check": key, "recorded": recorded, "file": relative, "outcome": None, "detail": ""}
        if recorded is None or not recorded.strip():
            check["outcome"] = "missing"
            check["detail"] = "no hash recorded"
        elif not HEX64_RE.match(recorded.strip()):
            check["outcome"] = "malformed"
            check["detail"] = "recorded hash is not a 64-character lowercase hex digest"
        elif not repo_file.is_file():
            check["outcome"] = "unverifiable"
            check["detail"] = f"input file missing in the current repository: {relative}"
        else:
            actual = sha256_file(repo_file)
            check["actual"] = actual
            if actual == recorded.strip():
                check["outcome"] = "match"
            else:
                check["outcome"] = "mismatch"
                check["detail"] = (
                    f"recorded {recorded.strip()} does not match the current "
                    f"repository file {relative} ({actual})"
                )
        checks.append(check)
        if check["outcome"] in ("mismatch", "malformed", "unverifiable"):
            add(PROVENANCE_MISMATCH, f"provenance {key}: {check['detail']}")

    side_paths = [
        ("bad_model_path", "bad", "model.json"),
        ("bad_properties_path", "bad", "properties.json"),
        ("control_model_path", "control", "model.json"),
        ("control_properties_path", "control", "properties.json"),
    ]
    for key, side, name in side_paths:
        recorded = values.get(key)
        if recorded is None:
            continue
        expected_suffix = f"{exp['benchmark_dir']}/{side}/{name}"
        if not recorded.strip().endswith(expected_suffix):
            add(PROVENANCE_MISMATCH, f"provenance {key}={recorded!r} does not refer to {expected_suffix}")

    for key, suffix in (
        ("console_dir", f"{cfg_id}/console"),
        ("pair_runner_arg_out_dir", f"{cfg_id}/console"),
        ("artifacts_base_dir", f"{cfg_id}/artifacts"),
        ("pair_runner_env_RACELOOM_OUTPUT_DIR", f"{cfg_id}/artifacts"),
    ):
        recorded = values.get(key)
        if recorded is None:
            continue
        if not recorded.strip().rstrip("/").endswith(suffix):
            add(PROVENANCE_MISMATCH, f"provenance {key}={recorded!r} does not refer to this configuration's .../{suffix} directory")

    for key in PROVENANCE_SCRIPT_FILES:
        recorded = values.get(key)
        if recorded is None:
            continue
        if not HEX64_RE.match(recorded.strip()):
            add(PROVENANCE_MISMATCH, f"provenance {key} is not a 64-character lowercase hex digest: {recorded!r}")
            continue
        current_file = repo_root / PROVENANCE_SCRIPT_FILES[key]
        if current_file.is_file():
            actual = sha256_file(current_file)
            if actual != recorded.strip():
                warnings.append(
                    f"provenance {key} differs from the current "
                    f"{PROVENANCE_SCRIPT_FILES[key]} (scripts may have changed "
                    "since execution; informational only)"
                )

    fingerprint = values.get("wt_fingerprint")
    if fingerprint is not None and not HEX64_RE.match(fingerprint.strip()):
        add(PROVENANCE_MISMATCH, f"provenance wt_fingerprint is not a 64-character hex digest: {fingerprint!r}")
    worktree_state = values.get("git_worktree_state")
    if worktree_state is not None and worktree_state not in ("clean", "dirty"):
        warnings.append(f"provenance git_worktree_state={worktree_state!r} is unexpected")
    resolved_image = values.get("resolved_image_id")
    if resolved_image is not None and not resolved_image.strip().startswith(("sha256:", "sha512:")):
        warnings.append(f"provenance resolved_image_id={resolved_image!r} does not look like a docker content-digest image ID")

    current_head = read_git_head(repo_root)
    recorded_head = values.get("git_head")
    if current_head and recorded_head and recorded_head.strip() != current_head:
        warnings.append(
            f"provenance git_head={recorded_head.strip()} differs from the current "
            f"repository HEAD {current_head} (informational only)"
        )


def evaluate_side(exp, cfg_dir, side, historical_side, add, warnings):
    depth = exp["depth"]
    console_rel = f"console/{exp['log_base']}_{side}_depth{depth}.log"
    csv_rel = f"artifacts/{side}/final_stats.csv"
    console_path = cfg_dir / console_rel
    csv_path = cfg_dir / csv_rel
    side_report = {
        "console_log": console_rel,
        "console_present": console_path.is_file(),
        "final_stats_csv": csv_rel,
        "csv_present": csv_path.is_file(),
        "console_fields": None,
        "console_timings": None,
        "csv_fields": None,
        "csv_timings": None,
        "console_csv_consistent": None,
        "science": {},
        "comparisons": [],
        "harmful_trace_evidence": None,
        "valid_evidence": False,
    }

    console = None
    if not console_path.is_file():
        add(INCOMPLETE_EVIDENCE, f"{side}: console log missing: {console_rel}")
    elif console_path.stat().st_size == 0:
        add(INCOMPLETE_EVIDENCE, f"{side}: console log is empty: {console_rel}")
    else:
        console, console_issues = parse_console_log(console_path)
        for issue in console_issues:
            add(INCOMPLETE_EVIDENCE, f"{side}: {issue}")
        side_report["console_fields"] = console["science"]
        side_report["console_timings"] = console["timings"]
        for key in REQUIRED_CONSOLE_SCIENCE:
            if console["science"].get(key) is None:
                add(INCOMPLETE_EVIDENCE, f"{side}: console log Final Stats block lacks a usable {key} value")
        if not console["output_written"]:
            warnings.append(f"{side}: console log does not contain an 'Output written to:' line")

    csv_data = None
    if not csv_path.is_file():
        add(INCOMPLETE_EVIDENCE, f"{side}: final_stats.csv missing: {csv_rel}")
    elif csv_path.stat().st_size == 0:
        add(INCOMPLETE_EVIDENCE, f"{side}: final_stats.csv is empty: {csv_rel}")
    else:
        csv_data, csv_issues = parse_final_stats_csv(csv_path)
        for issue in csv_issues:
            add(INCOMPLETE_EVIDENCE, f"{side}: {issue}")
        if csv_data is not None:
            side_report["csv_fields"] = csv_data["science"]
            side_report["csv_timings"] = csv_data["timings"]

    consistent = None
    if console is not None and csv_data is not None:
        conflicts = []
        for column, key in CSV_TO_SCIENCE.items():
            console_value = console["science"].get(key)
            csv_value = csv_data["science"].get(key)
            if console_value is None or csv_value is None:
                continue
            if console_value != csv_value:
                conflicts.append(f"{key}: console={console_value!r} vs final_stats.csv={csv_value!r}")
        if conflicts:
            consistent = False
            add(INCOMPLETE_EVIDENCE, f"{side}: console log and final_stats.csv disagree ({'; '.join(conflicts)})")
        else:
            consistent = True
    side_report["console_csv_consistent"] = consistent

    agreed = {}
    if consistent:
        for key in REQUIRED_CONSOLE_SCIENCE:
            value = csv_data["science"].get(key)
            if value is not None:
                agreed[key] = value
    side_report["science"] = agreed

    expected_map = {
        "traces": exp["traces"],
        "harmful": exp["bad_harmful"] if side == "bad" else exp["control_harmful"],
        "branches": exp["branches"],
        "depth": exp["depth"],
        "strategy": EXPECTED_STRATEGY,
    }
    for key, expected in expected_map.items():
        actual = agreed.get(key)
        if key == "branches":
            side_report["comparisons"].append(
                branch_signature_comparison(side, expected, actual, add))
            continue
        if actual is None:
            comparison = {"field": key, "expected": expected, "actual": actual, "outcome": "unavailable", "source": "matrix_tsv"}
        elif actual == expected:
            comparison = {"field": key, "expected": expected, "actual": actual, "outcome": "match", "source": "matrix_tsv"}
        else:
            comparison = {"field": key, "expected": expected, "actual": actual, "outcome": "mismatch", "source": "matrix_tsv"}
            add(SCIENTIFIC_MISMATCH, f"{side}: {key} expected {expected!r} (matrix TSV), actual {actual!r}")
        side_report["comparisons"].append(comparison)

    if agreed:
        if historical_side is None:
            side_report["comparisons"].append({
                "field": "cache_counters", "expected": None, "actual": None,
                "outcome": "unavailable", "source": "historical_log",
                "note": "no historical log available for this side",
            })
        else:
            for key in ("gen_cache_hits", "gen_cache_misses", "katch_cache_hits", "katch_cache_misses"):
                expected = historical_side["cache"].get(key)
                actual = agreed.get(key)
                if expected is None:
                    side_report["comparisons"].append({
                        "field": key, "expected": None, "actual": actual,
                        "outcome": "unavailable", "source": "historical_log",
                        "note": "counter not extractable from the historical log",
                    })
                    warnings.append(f"{side}: historical cache counter {key} is unavailable for comparison")
                elif actual is None:
                    side_report["comparisons"].append({
                        "field": key, "expected": expected, "actual": None,
                        "outcome": "unavailable", "source": "historical_log",
                    })
                else:
                    outcome = "match" if actual == expected else "mismatch"
                    side_report["comparisons"].append({
                        "field": key, "expected": expected, "actual": actual,
                        "outcome": outcome, "source": "historical_log",
                    })
                    if outcome == "mismatch":
                        add(SCIENTIFIC_MISMATCH, f"{side}: {key} expected {expected} (historical log), actual {actual}")

    side_dir = cfg_dir / "artifacts" / side
    run_dirs = sorted(entry for entry in side_dir.glob("run_*") if entry.is_dir()) if side_dir.is_dir() else []
    trace_files = sum(count_files(run_dir / "harmful_traces") for run_dir in run_dirs)
    raw_files = sum(count_files(run_dir / "harmful_traces_raw") for run_dir in run_dirs)
    harmful_value = agreed.get("harmful")
    if harmful_value is None:
        hte = {"harmful": None, "run_dirs": len(run_dirs), "harmful_trace_files": trace_files, "harmful_trace_raw_files": raw_files, "outcome": "unavailable"}
    elif harmful_value > 0:
        if trace_files == 0:
            hte = {"harmful": harmful_value, "run_dirs": len(run_dirs), "harmful_trace_files": 0, "harmful_trace_raw_files": raw_files, "outcome": "missing"}
            add(INCOMPLETE_EVIDENCE, f"{side}: {harmful_value} harmful races reported but no preserved harmful trace files exist under artifacts/{side}/run_*/harmful_traces")
        else:
            hte = {"harmful": harmful_value, "run_dirs": len(run_dirs), "harmful_trace_files": trace_files, "harmful_trace_raw_files": raw_files, "outcome": "present"}
    else:
        if trace_files > 0:
            warnings.append(f"{side}: zero harmful races reported but {trace_files} harmful trace files are present under artifacts/{side}/run_*/harmful_traces")
        hte = {"harmful": 0, "run_dirs": len(run_dirs), "harmful_trace_files": trace_files, "harmful_trace_raw_files": raw_files, "outcome": "not_required"}
    side_report["harmful_trace_evidence"] = hte

    side_report["valid_evidence"] = bool(
        console is not None
        and csv_data is not None
        and consistent
        and all(console["science"].get(key) is not None for key in REQUIRED_CONSOLE_SCIENCE)
    )
    return side_report


def evaluate_config(exp, matrix_root, repo_root, records, historical):
    cfg_id = exp["config_id"]
    cfg_dir = matrix_root / cfg_id
    issues = []
    warnings = []

    def add(category, detail):
        issues.append({"category": category, "detail": detail})

    depth_str = str(exp["depth"])
    expected_depth_for_k = 5 if exp["k"] == "K8" else 4
    if exp["depth"] != expected_depth_for_k:
        warnings.append(
            f"matrix TSV depth={exp['depth']} for {exp['k']} differs from the "
            "historically required mapping (K8: 5, K12/K14/K16: 4)"
        )
    for side in SIDES:
        hist = historical.get(side)
        if not hist:
            continue
        header = hist["header"]
        hist_traces = typed_int(header.get("expected_traces"))
        if hist_traces is not None and hist_traces != exp["traces"]:
            warnings.append(
                f"historical log {side} expected_traces={hist_traces} disagrees with "
                f"matrix TSV traces={exp['traces']}; matrix TSV takes precedence"
            )
        tsv_harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
        hist_harmful = typed_int(header.get("expected_harmful"))
        if hist_harmful is not None and hist_harmful != tsv_harmful:
            warnings.append(
                f"historical log {side} expected_harmful={hist_harmful} disagrees with "
                f"matrix TSV harmful={tsv_harmful}; matrix TSV takes precedence"
            )
        hist_depth = typed_int(header.get("depth"))
        if hist_depth is not None and hist_depth != exp["depth"]:
            warnings.append(
                f"historical log {side} depth={hist_depth} disagrees with matrix TSV "
                f"depth={exp['depth']}; matrix TSV takes precedence"
            )

    report = {
        "config_id": cfg_id,
        "benchmark_tsv": exp["benchmark_tsv"],
        "topology": exp["topology"],
        "k": exp["k"],
        "benchmark_dir": exp["benchmark_dir"],
        "expected": {
            "depth": exp["depth"],
            "strategy": EXPECTED_STRATEGY,
            "branches": exp["branches"],
            "traces": exp["traces"],
            "bad_harmful": exp["bad_harmful"],
            "control_harmful": exp["control_harmful"],
            "historical_cache": {
                side: (historical[side]["cache"] if historical.get(side) else None)
                for side in SIDES
            },
        },
        "configuration_dir_present": cfg_dir.is_dir() and not cfg_dir.is_symlink(),
        "status_records": records,
        "operational": {},
        "provenance": {},
        "sides": {},
        "issues": issues,
        "warnings": warnings,
    }

    if cfg_dir.is_symlink():
        add(INCOMPLETE_EVIDENCE, f"configuration path is a symlink: {cfg_dir}")
    if not cfg_dir.is_dir():
        if records:
            add(INCOMPLETE_EVIDENCE, "status.tsv records exist for this configuration but its configuration directory is missing")
            report["classification"] = INCOMPLETE_EVIDENCE
        else:
            report["classification"] = NOT_RUN
        report["operational"] = {"configuration_directory": str(cfg_dir), "present": False}
        report["provenance"] = {"present": False, "record": None, "checks": []}
        for side in SIDES:
            report["sides"][side] = {"evidence_present": False}
        return report

    complete_marker_path = cfg_dir / COMPLETE_MARKER
    in_progress_path = cfg_dir / IN_PROGRESS_MARKER

    complete_marker = None
    if complete_marker_path.is_file():
        values, kv_issues = parse_kv_text(read_text(complete_marker_path))
        complete_marker = values
        for issue in kv_issues:
            add(INCOMPLETE_EVIDENCE, f"{COMPLETE_MARKER}: {issue}")
        if values.get("config_id") != cfg_id:
            add(INCOMPLETE_EVIDENCE, f"{COMPLETE_MARKER} config_id={values.get('config_id')!r} does not match expected {cfg_id!r}")
        if values.get("depth") != depth_str:
            add(INCOMPLETE_EVIDENCE, f"{COMPLETE_MARKER} depth={values.get('depth')!r} does not match expected {depth_str!r}")
        marker_exit = values.get("exit_code")
        if marker_exit is not None and marker_exit not in ("", "-", "0"):
            add(INFRASTRUCTURE_FAILURE, f"{COMPLETE_MARKER} records nonzero exit_code={marker_exit!r}")

    in_progress = None
    if in_progress_path.is_file():
        values, kv_issues = parse_kv_text(read_text(in_progress_path))
        in_progress = values
        for issue in kv_issues:
            add(INCOMPLETE_EVIDENCE, f"{IN_PROGRESS_MARKER}: {issue}")
        add(INCOMPLETE_EVIDENCE, "interrupted or in-progress execution: STATUS_IN_PROGRESS marker is present")
    if complete_marker_path.is_file() and in_progress_path.is_file():
        add(INCOMPLETE_EVIDENCE, "contradictory completion evidence: both STATUS_COMPLETE and STATUS_IN_PROGRESS markers exist")

    last_record = records[-1] if records else None
    report["operational"] = {
        "configuration_directory": str(cfg_dir),
        "present": True,
        "record_count": len(records),
        "last_status": last_record["status"] if last_record else None,
        "last_exit_code": last_record["exit_code"] if last_record else None,
        "complete_marker_present": complete_marker_path.is_file(),
        "in_progress_marker_present": in_progress_path.is_file(),
        "complete_marker": complete_marker,
        "in_progress_marker": in_progress,
    }

    if last_record:
        status_value = last_record["status"]
        if status_value not in STATUS_VALUES:
            add(INCOMPLETE_EVIDENCE, f"status.tsv records unrecognized status {status_value!r}")
        elif status_value not in OPERATIONAL_SUCCESS_STATUSES:
            if status_value == "FAILED" or any(r.get("status") == "FAILED" for r in records):
                add(INFRASTRUCTURE_FAILURE, (
                    f"status.tsv records execution failure (status={status_value!r}, "
                    f"exit_code={last_record.get('exit_code')!r}, "
                    f"detail={last_record.get('detail')!r})"
                ))
            else:
                add(INCOMPLETE_EVIDENCE, f"status.tsv records {status_value} ({last_record.get('detail')!r}); operational completion not established")
        else:
            exit_code = last_record.get("exit_code")
            if exit_code not in ("", "-", "0"):
                add(INFRASTRUCTURE_FAILURE, f"status.tsv records operational success with nonzero exit_code={exit_code!r}")
            if last_record.get("benchmark") not in (None, exp["benchmark_dir"]):
                add(INCOMPLETE_EVIDENCE, f"status.tsv record benchmark={last_record.get('benchmark')!r} does not match {exp['benchmark_dir']!r}")
            if last_record.get("depth") != depth_str:
                add(INCOMPLETE_EVIDENCE, f"status.tsv record depth={last_record.get('depth')!r} does not match expected {depth_str!r}")
            evidence_dir = last_record.get("evidence_dir")
            if evidence_dir and not (evidence_dir == str(cfg_dir) or evidence_dir.rstrip("/").endswith(f"/{cfg_id}")):
                warnings.append(f"status.tsv evidence_dir={evidence_dir!r} does not clearly refer to this configuration directory")
    if complete_marker_path.is_file() and last_record is None:
        add(INCOMPLETE_EVIDENCE, f"{COMPLETE_MARKER} marker exists but status.tsv contains no record for this configuration")
    if last_record and last_record.get("status") in OPERATIONAL_SUCCESS_STATUSES and not complete_marker_path.is_file():
        add(INCOMPLETE_EVIDENCE, "status.tsv records operational completion but the STATUS_COMPLETE marker is missing")

    provenance_path = cfg_dir / PROVENANCE_NAME
    provenance_report = {"present": provenance_path.is_file(), "record": None, "checks": []}
    report["provenance"] = provenance_report
    if not provenance_path.is_file():
        add(INCOMPLETE_EVIDENCE, f"provenance record missing: {PROVENANCE_NAME}")
    elif provenance_path.stat().st_size == 0:
        add(INCOMPLETE_EVIDENCE, "provenance record is empty")
    else:
        values, kv_issues = parse_kv_text(read_text(provenance_path))
        provenance_report["record"] = values
        for issue in kv_issues:
            add(INCOMPLETE_EVIDENCE, f"{PROVENANCE_NAME}: {issue}")
        evaluate_provenance(exp, repo_root, values, provenance_report["checks"], add, warnings)

    for side in SIDES:
        report["sides"][side] = evaluate_side(exp, cfg_dir, side, historical.get(side), add, warnings)

    if issues:
        report["classification"] = min(
            (issue["category"] for issue in issues),
            key=lambda category: CLASSIFICATION_PRECEDENCE[category],
        )
    else:
        report["classification"] = SCIENTIFIC_MATCH
    return report


def build_report(matrix_root, repo_root, expectations, order, status_records, status_present, status_warnings, historical_logs_found):
    configurations = []
    for config_id in order:
        exp = expectations[config_id]
        records = [record for record in status_records if record.get("config_id") == config_id]
        historical = {}
        for side in SIDES:
            try:
                historical[side] = load_historical_log(repo_root, config_id, side)
            except OSError:
                historical[side] = None
        try:
            config_report = evaluate_config(exp, matrix_root, repo_root, records, historical)
        except Exception as exc:
            config_report = {
                "config_id": config_id,
                "benchmark_tsv": exp["benchmark_tsv"],
                "topology": exp["topology"],
                "k": exp["k"],
                "benchmark_dir": exp["benchmark_dir"],
                "expected": {
                    "depth": exp["depth"],
                    "strategy": EXPECTED_STRATEGY,
                    "branches": exp["branches"],
                    "traces": exp["traces"],
                    "bad_harmful": exp["bad_harmful"],
                    "control_harmful": exp["control_harmful"],
                    "historical_cache": {side: None for side in SIDES},
                },
                "classification": INCOMPLETE_EVIDENCE,
                "configuration_dir_present": None,
                "status_records": records,
                "operational": {},
                "provenance": {"present": None, "record": None, "checks": []},
                "sides": {side: {"evidence_present": None} for side in SIDES},
                "issues": [{
                    "category": INCOMPLETE_EVIDENCE,
                    "detail": f"internal evaluation error: {exc.__class__.__name__}: {exc}",
                }],
                "warnings": [],
            }
        configurations.append(config_report)

    classification_counts = {}
    for config_report in configurations:
        classification = config_report["classification"]
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
    sides_valid = sum(
        1
        for config_report in configurations
        for side in SIDES
        if config_report["sides"].get(side, {}).get("valid_evidence")
    )
    success = all(config_report["classification"] == SCIENTIFIC_MATCH for config_report in configurations)
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matrix_root": str(matrix_root),
        "repo_root": str(repo_root),
        "expectations": {
            "matrix_tsv": MATRIX_TSV_RELATIVE.as_posix(),
            "historical_logs_dir": HISTORICAL_LOGS_RELATIVE.as_posix(),
            "historical_logs_found": historical_logs_found,
            "strategy": EXPECTED_STRATEGY,
            "total_configurations": len(configurations),
        },
        "timing_policy": TIMING_POLICY,
        "status_file": {"present": status_present, "warnings": status_warnings},
        "overall": {
            "success": success,
            "total_configurations": len(configurations),
            "classification_counts": classification_counts,
            "sides_with_valid_evidence": sides_valid,
            "sides_total": 2 * len(configurations),
        },
        "configurations": configurations,
    }


def science_summary(config_report):
    parts = []
    for side in SIDES:
        science = config_report["sides"].get(side, {}).get("science")
        if science and science.get("traces") is not None:
            parts.append(f"{side}: traces={science['traces']} harmful={science.get('harmful')}")
        else:
            parts.append(f"{side}: no evidence")
    return "; ".join(parts)


def render_human(report):
    out = []
    out.append("RaceLoom-Bench final matrix scientific checker")
    out.append(f"schema: {SCHEMA}")
    out.append(f"matrix root: {report['matrix_root']}")
    out.append(f"repository:  {report['repo_root']}")
    expectations_meta = report["expectations"]
    out.append(
        f"expectations: {expectations_meta['matrix_tsv']} "
        f"({expectations_meta['total_configurations']} configurations), "
        f"{expectations_meta['historical_logs_dir']} "
        f"({expectations_meta['historical_logs_found']} historical logs)"
    )
    out.append(f"timing policy: {report['timing_policy']}")
    out.append("")
    out.append("per-configuration results:")
    for config_report in report["configurations"]:
        out.append(
            f"  {config_report['config_id']:<24} "
            f"{config_report['classification']:<22} {science_summary(config_report)}"
        )
    nonmatching = [c for c in report["configurations"] if c["classification"] != SCIENTIFIC_MATCH]
    if nonmatching:
        out.append("")
        out.append("findings:")
        for config_report in nonmatching:
            out.append(f"  [{config_report['config_id']}] {config_report['classification']}")
            for issue in config_report["issues"]:
                out.append(f"    - ({issue['category']}) {issue['detail']}")
    warnings = list(report["status_file"].get("warnings") or [])
    for config_report in report["configurations"]:
        warnings.extend(config_report.get("warnings") or [])
    if warnings:
        out.append("")
        out.append("warnings:")
        for warning in warnings:
            out.append(f"  - {warning}")
    counts = report["overall"]["classification_counts"]
    out.append("")
    out.append("summary:")
    out.append(f"  configurations checked: {report['overall']['total_configurations']}")
    for classification in ALL_CLASSIFICATIONS:
        out.append(f"  {classification}: {counts.get(classification, 0)}")
    out.append(
        f"  sides with valid evidence: "
        f"{report['overall']['sides_with_valid_evidence']}/{report['overall']['sides_total']}"
    )
    matched = counts.get(SCIENTIFIC_MATCH, 0)
    if report["overall"]["success"]:
        out.append("OVERALL: PASS - all 16 configurations scientifically matched")
    else:
        out.append(
            f"OVERALL: FAIL - {matched}/{report['overall']['total_configurations']} "
            "configurations scientifically matched"
        )
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_final_matrix.py",
        description="Read-only scientific result checker for the RaceLoom-Bench final 4x4 matrix.",
    )
    parser.add_argument(
        "--matrix-root",
        required=True,
        help="existing matrix output root produced by scripts/run_final_matrix.sh",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="benchmark repository root (default: the repository containing this script)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable JSON report to stdout",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="write the JSON report to a new file (refuses to overwrite existing files)",
    )
    args = parser.parse_args(argv)

    matrix_root = Path(args.matrix_root).expanduser()
    if not matrix_root.is_dir():
        print(f"ERROR: matrix root is not an existing directory: {matrix_root}", file=sys.stderr)
        return 2
    matrix_root = matrix_root.resolve()

    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser().resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent

    try:
        expectations, order = load_matrix_tsv(repo_root)
        resolve_benchmark_dirs(repo_root, expectations)
    except ExpectationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    status_path = matrix_root / STATUS_TSV_NAME
    status_present = status_path.is_file()
    status_records = []
    status_warnings = []
    if status_present:
        status_records, status_issues, header_ok = parse_status_tsv(status_path)
        if not header_ok:
            print(
                "ERROR: status.tsv does not match the expected matrix status schema; "
                "refusing to interpret this matrix root",
                file=sys.stderr,
            )
            return 2
        status_warnings = list(status_issues)

    historical_dir = repo_root / HISTORICAL_LOGS_RELATIVE
    historical_logs_found = len(list(historical_dir.glob("*.txt"))) if historical_dir.is_dir() else 0

    report = build_report(
        matrix_root, repo_root, expectations, order,
        status_records, status_present, status_warnings, historical_logs_found,
    )
    json_text = json.dumps(report, indent=2) + "\n"

    if args.output:
        output_path = Path(args.output).expanduser()
        if output_path.exists() or output_path.is_symlink():
            print(f"ERROR: refusing to overwrite an existing file: {output_path}", file=sys.stderr)
            return 2
        if not output_path.parent.is_dir():
            print(f"ERROR: output directory does not exist: {output_path.parent}", file=sys.stderr)
            return 2
        try:
            output_path.write_text(json_text, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write report: {exc}", file=sys.stderr)
            return 2

    if args.json:
        sys.stdout.write(json_text)
    else:
        sys.stdout.write(render_human(report))

    return 0 if report["overall"]["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
