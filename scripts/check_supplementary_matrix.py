#!/usr/bin/env python3
"""Independent, read-only scientific result checker for the supplementary
RaceLoom-Bench S1-S4 synthetic benchmark group (Increment 43).

Compares newly generated supplementary evidence (console logs, side-root
final_stats.csv files, completion markers, status.tsv records and
per-configuration provenance) against the historical expectations recorded in
docs/synthetic_s1_s4_matrix.tsv and docs/validation_logs/synthetic/. The
checker never executes RaceLoom or Docker, never modifies any input or
evidence file, and uses the Python 3 standard library only.

This checker is deliberately separate from scripts/check_final_matrix.py: the
synthetic group has a different expectation schema (ID/Scenario/Depth/...),
different historical log names (S<n>_<side>.txt) and no principal-matrix
family/topology depth mapping. It reuses the principal checker's tested
parsing and evaluation components, including the order-independent
branch-signature comparison introduced in Increment 42: branch signatures
("Name:count;Name:count;...") are compared as branch-name/count mappings, the
original signature strings are preserved in reports, and malformed signatures
or duplicate branch names are rejected and can never produce a match.

Usage:
    python3 scripts/check_supplementary_matrix.py --matrix-root /path/to/root
    python3 scripts/check_supplementary_matrix.py --matrix-root ROOT --json
    python3 scripts/check_supplementary_matrix.py --matrix-root ROOT --output report.json

Exit codes:
    0  all 4 configurations are SCIENTIFIC_MATCH
    1  validation unsuccessful (any other classification)
    2  environment or usage error (missing expectation sources, malformed
       synthetic TSV, unreadable matrix root, ...)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import check_final_matrix as checker

SCHEMA = "raceloom-supplementary-check-report-v1"
EXPECTED_CONFIG_COUNT = 4

SYNTHETIC_TSV_RELATIVE = Path("docs") / "synthetic_s1_s4_matrix.tsv"
HISTORICAL_LOGS_RELATIVE = Path("docs") / "validation_logs" / "synthetic"
BENCHMARKS_SYNTHETIC_FINAL_RELATIVE = Path("benchmarks") / "synthetic" / "final"

# The supplementary launcher records the hash of the executing launcher script
# (scripts/run_supplementary_matrix.sh) under the provenance schema-v1 key
# sha256_run_final_matrix_sh. Point the reused provenance evaluation at the
# supplementary launcher for that key; this process-local override does not
# affect the principal checker's own runs.
checker.PROVENANCE_SCRIPT_FILES = dict(checker.PROVENANCE_SCRIPT_FILES)
checker.PROVENANCE_SCRIPT_FILES["sha256_run_final_matrix_sh"] = (
    "scripts/run_supplementary_matrix.sh"
)

SYNTHETIC_TSV_COLUMNS = [
    "id", "scenario", "depth", "strategy", "branches", "traces",
    "bad_harmful", "control_harmful", "bad_total_seconds", "control_total_seconds",
]

SYNTHETIC_TSV_EXPECTED_HEADER = [
    "ID", "Scenario", "Depth", "Strategy", "Branch structure",
    "Generated traces", "Bad harmful races", "Control harmful races",
    "Bad total seconds", "Control total seconds",
]

class ExpectationError(Exception):
    pass


def load_synthetic_tsv(repo_root):
    path = repo_root / SYNTHETIC_TSV_RELATIVE
    if not path.is_file():
        raise ExpectationError(f"synthetic TSV not found: {path}")
    text = checker.read_text(path)
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ExpectationError(f"synthetic TSV has no data rows: {path}")
    header = lines[0].split("\t")
    if header != SYNTHETIC_TSV_EXPECTED_HEADER:
        raise ExpectationError(
            f"synthetic TSV header does not match the expected schema "
            f"{SYNTHETIC_TSV_EXPECTED_HEADER!r}: {header!r}"
        )
    expectations = {}
    order = []
    for lineno, line in enumerate(lines[1:], 2):
        parts = line.split("\t")
        if len(parts) != len(SYNTHETIC_TSV_COLUMNS):
            raise ExpectationError(
                f"synthetic TSV line {lineno}: expected {len(SYNTHETIC_TSV_COLUMNS)} "
                f"tab-separated fields, found {len(parts)}"
            )
        row = dict(zip(SYNTHETIC_TSV_COLUMNS, parts))
        s_id = row["id"].strip()
        if not s_id or not s_id.startswith("S") or not s_id[1:].isdigit():
            raise ExpectationError(
                f"synthetic TSV line {lineno}: id {row['id']!r} is not an S<n> identifier"
            )
        for column in ("depth", "traces", "bad_harmful", "control_harmful"):
            if not row[column].strip().isdigit():
                raise ExpectationError(
                    f"synthetic TSV line {lineno}: column {column} is not a "
                    f"non-negative integer: {row[column]!r}"
                )
        if row["strategy"].strip() != checker.EXPECTED_STRATEGY:
            raise ExpectationError(
                f"synthetic TSV line {lineno}: strategy {row['strategy']!r} "
                f"does not match the expected strategy {checker.EXPECTED_STRATEGY!r}"
            )
        benchmark_dir = resolve_synthetic_benchmark_dir(repo_root, s_id)
        config_id = benchmark_dir.rsplit("/", 1)[-1]
        config_id = config_id[0].upper() + config_id[1:]
        if config_id in expectations:
            raise ExpectationError(
                f"synthetic TSV line {lineno}: duplicate configuration {config_id}"
            )
        expectations[config_id] = {
            "config_id": config_id,
            "s_id": s_id,
            "scenario": row["scenario"],
            "depth": int(row["depth"]),
            "strategy": row["strategy"].strip(),
            "branches": row["branches"],
            "traces": int(row["traces"]),
            "bad_harmful": int(row["bad_harmful"]),
            "control_harmful": int(row["control_harmful"]),
            "bad_total_seconds": row["bad_total_seconds"],
            "control_total_seconds": row["control_total_seconds"],
            "benchmark_dir": benchmark_dir,
            "log_base": benchmark_dir.replace("/", "_"),
            "tsv_line": lineno,
        }
        order.append(config_id)
    if len(expectations) != EXPECTED_CONFIG_COUNT:
        raise ExpectationError(
            f"synthetic TSV must describe exactly {EXPECTED_CONFIG_COUNT} "
            f"configurations, found {len(expectations)}"
        )
    return expectations, order


def resolve_synthetic_benchmark_dir(repo_root, s_id):
    base = repo_root / BENCHMARKS_SYNTHETIC_FINAL_RELATIVE
    if not base.is_dir():
        raise ExpectationError(f"synthetic benchmark root not found: {base}")
    prefix = s_id.lower() + "_"
    matches = sorted(
        entry.name for entry in base.iterdir()
        if entry.is_dir() and entry.name.startswith(prefix)
    )
    if len(matches) != 1:
        raise ExpectationError(
            f"synthetic benchmark {s_id}: expected exactly one directory starting "
            f"with {prefix!r} under {BENCHMARKS_SYNTHETIC_FINAL_RELATIVE.as_posix()}, "
            f"found {matches!r}"
        )
    return f"{BENCHMARKS_SYNTHETIC_FINAL_RELATIVE.as_posix()}/{matches[0]}"


def load_synthetic_historical_log(repo_root, s_id, side):
    path = repo_root / HISTORICAL_LOGS_RELATIVE / f"{s_id}_{side}.txt"
    if not path.is_file():
        return None
    text = checker.read_text(path)
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
    block, _terminated = checker.extract_final_stats_block(text)
    fields = checker.parse_stats_fields(block) if block is not None else {}
    cache = {}
    for key, label in (
        ("gen_cache_hits", "Trace generation cache hits"),
        ("gen_cache_misses", "Trace generation cache misses"),
        ("katch_cache_hits", "KATch total cache hits"),
        ("katch_cache_misses", "KATch total cache misses"),
    ):
        value = checker.typed_int(fields.get(label))
        if value is not None:
            cache[key] = value
    return {
        "path": path,
        "header": header,
        "cache": cache,
        "traces": checker.typed_int(fields.get("Generated traces")),
        "harmful": checker.typed_int(fields.get("Harmful races found")),
        "branches": fields.get("Network model branches"),
        "depth": checker.typed_int(fields.get("Depth")),
        "strategy": fields.get("Trace generation strategy"),
    }


def evaluate_synthetic_config(exp, matrix_root, repo_root, records, historical):
    cfg_id = exp["config_id"]
    cfg_dir = matrix_root / cfg_id
    issues = []
    warnings = []

    def add(category, detail):
        issues.append({"category": category, "detail": detail})

    depth_str = str(exp["depth"])
    for side in checker.SIDES:
        hist = historical.get(side)
        if not hist:
            continue
        header = hist["header"]
        hist_traces = checker.typed_int(header.get("expected_traces"))
        if hist_traces is not None and hist_traces != exp["traces"]:
            warnings.append(
                f"historical log {side} expected_traces={hist_traces} disagrees with "
                f"synthetic TSV traces={exp['traces']}; synthetic TSV takes precedence"
            )
        tsv_harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
        hist_harmful = checker.typed_int(header.get("expected_harmful"))
        if hist_harmful is not None and hist_harmful != tsv_harmful:
            warnings.append(
                f"historical log {side} expected_harmful={hist_harmful} disagrees with "
                f"synthetic TSV harmful={tsv_harmful}; synthetic TSV takes precedence"
            )
        hist_depth = checker.typed_int(header.get("depth"))
        if hist_depth is not None and hist_depth != exp["depth"]:
            warnings.append(
                f"historical log {side} depth={hist_depth} disagrees with synthetic TSV "
                f"depth={exp['depth']}; synthetic TSV takes precedence"
            )
        hist_strategy = header.get("strategy")
        if hist_strategy is not None and hist_strategy != exp["strategy"]:
            warnings.append(
                f"historical log {side} strategy={hist_strategy!r} disagrees with "
                f"synthetic TSV strategy={exp['strategy']!r}; synthetic TSV takes precedence"
            )

    report = {
        "config_id": cfg_id,
        "s_id": exp["s_id"],
        "scenario": exp["scenario"],
        "benchmark_dir": exp["benchmark_dir"],
        "expected": {
            "depth": exp["depth"],
            "strategy": exp["strategy"],
            "branches": exp["branches"],
            "traces": exp["traces"],
            "bad_harmful": exp["bad_harmful"],
            "control_harmful": exp["control_harmful"],
            "historical_total_seconds": {
                "bad": exp["bad_total_seconds"],
                "control": exp["control_total_seconds"],
            },
            "historical_cache": {
                side: (historical[side]["cache"] if historical.get(side) else None)
                for side in checker.SIDES
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
        add(checker.INCOMPLETE_EVIDENCE, f"configuration path is a symlink: {cfg_dir}")
    if not cfg_dir.is_dir():
        if records:
            add(checker.INCOMPLETE_EVIDENCE, "status.tsv records exist for this configuration but its configuration directory is missing")
            report["classification"] = checker.INCOMPLETE_EVIDENCE
        else:
            report["classification"] = checker.NOT_RUN
        report["operational"] = {"configuration_directory": str(cfg_dir), "present": False}
        report["provenance"] = {"present": False, "record": None, "checks": []}
        for side in checker.SIDES:
            report["sides"][side] = {"evidence_present": False}
        return report

    complete_marker_path = cfg_dir / checker.COMPLETE_MARKER
    in_progress_path = cfg_dir / checker.IN_PROGRESS_MARKER

    complete_marker = None
    if complete_marker_path.is_file():
        values, kv_issues = checker.parse_kv_text(checker.read_text(complete_marker_path))
        complete_marker = values
        for issue in kv_issues:
            add(checker.INCOMPLETE_EVIDENCE, f"{checker.COMPLETE_MARKER}: {issue}")
        if values.get("config_id") != cfg_id:
            add(checker.INCOMPLETE_EVIDENCE, f"{checker.COMPLETE_MARKER} config_id={values.get('config_id')!r} does not match expected {cfg_id!r}")
        if values.get("depth") != depth_str:
            add(checker.INCOMPLETE_EVIDENCE, f"{checker.COMPLETE_MARKER} depth={values.get('depth')!r} does not match expected {depth_str!r}")
        marker_exit = values.get("exit_code")
        if marker_exit is not None and marker_exit not in ("", "-", "0"):
            add(checker.INFRASTRUCTURE_FAILURE, f"{checker.COMPLETE_MARKER} records nonzero exit_code={marker_exit!r}")

    in_progress = None
    if in_progress_path.is_file():
        values, kv_issues = checker.parse_kv_text(checker.read_text(in_progress_path))
        in_progress = values
        for issue in kv_issues:
            add(checker.INCOMPLETE_EVIDENCE, f"{checker.IN_PROGRESS_MARKER}: {issue}")
        add(checker.INCOMPLETE_EVIDENCE, "interrupted or in-progress execution: STATUS_IN_PROGRESS marker is present")
    if complete_marker_path.is_file() and in_progress_path.is_file():
        add(checker.INCOMPLETE_EVIDENCE, "contradictory completion evidence: both STATUS_COMPLETE and STATUS_IN_PROGRESS markers exist")

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
        if status_value not in checker.STATUS_VALUES:
            add(checker.INCOMPLETE_EVIDENCE, f"status.tsv records unrecognized status {status_value!r}")
        elif status_value not in checker.OPERATIONAL_SUCCESS_STATUSES:
            if status_value == "FAILED" or any(r.get("status") == "FAILED" for r in records):
                add(checker.INFRASTRUCTURE_FAILURE, (
                    f"status.tsv records execution failure (status={status_value!r}, "
                    f"exit_code={last_record.get('exit_code')!r}, "
                    f"detail={last_record.get('detail')!r})"
                ))
            else:
                add(checker.INCOMPLETE_EVIDENCE, f"status.tsv records {status_value} ({last_record.get('detail')!r}); operational completion not established")
        else:
            exit_code = last_record.get("exit_code")
            if exit_code not in ("", "-", "0"):
                add(checker.INFRASTRUCTURE_FAILURE, f"status.tsv records operational success with nonzero exit_code={exit_code!r}")
            if last_record.get("benchmark") not in (None, exp["benchmark_dir"]):
                add(checker.INCOMPLETE_EVIDENCE, f"status.tsv record benchmark={last_record.get('benchmark')!r} does not match {exp['benchmark_dir']!r}")
            if last_record.get("depth") != depth_str:
                add(checker.INCOMPLETE_EVIDENCE, f"status.tsv record depth={last_record.get('depth')!r} does not match expected {depth_str!r}")
            evidence_dir = last_record.get("evidence_dir")
            if evidence_dir and not (evidence_dir == str(cfg_dir) or evidence_dir.rstrip("/").endswith(f"/{cfg_id}")):
                warnings.append(f"status.tsv evidence_dir={evidence_dir!r} does not clearly refer to this configuration directory")
    if complete_marker_path.is_file() and last_record is None:
        add(checker.INCOMPLETE_EVIDENCE, f"{checker.COMPLETE_MARKER} marker exists but status.tsv contains no record for this configuration")
    if last_record and last_record.get("status") in checker.OPERATIONAL_SUCCESS_STATUSES and not complete_marker_path.is_file():
        add(checker.INCOMPLETE_EVIDENCE, "status.tsv records operational completion but the STATUS_COMPLETE marker is missing")

    provenance_path = cfg_dir / checker.PROVENANCE_NAME
    provenance_report = {"present": provenance_path.is_file(), "record": None, "checks": []}
    report["provenance"] = provenance_report
    if not provenance_path.is_file():
        add(checker.INCOMPLETE_EVIDENCE, f"provenance record missing: {checker.PROVENANCE_NAME}")
    elif provenance_path.stat().st_size == 0:
        add(checker.INCOMPLETE_EVIDENCE, "provenance record is empty")
    else:
        values, kv_issues = checker.parse_kv_text(checker.read_text(provenance_path))
        provenance_report["record"] = values
        for issue in kv_issues:
            add(checker.INCOMPLETE_EVIDENCE, f"{checker.PROVENANCE_NAME}: {issue}")
        checker.evaluate_provenance(exp, repo_root, values, provenance_report["checks"], add, warnings)

    for side in checker.SIDES:
        report["sides"][side] = checker.evaluate_side(exp, cfg_dir, side, historical.get(side), add, warnings)

    if issues:
        report["classification"] = min(
            (issue["category"] for issue in issues),
            key=lambda category: checker.CLASSIFICATION_PRECEDENCE[category],
        )
    else:
        report["classification"] = checker.SCIENTIFIC_MATCH
    return report


def build_report(matrix_root, repo_root, expectations, order, status_records, status_present, status_warnings, historical_logs_found):
    configurations = []
    for config_id in order:
        exp = expectations[config_id]
        records = [record for record in status_records if record.get("config_id") == config_id]
        historical = {}
        for side in checker.SIDES:
            try:
                historical[side] = load_synthetic_historical_log(repo_root, exp["s_id"], side)
            except OSError:
                historical[side] = None
        try:
            config_report = evaluate_synthetic_config(exp, matrix_root, repo_root, records, historical)
        except Exception as exc:
            config_report = {
                "config_id": config_id,
                "s_id": exp["s_id"],
                "scenario": exp["scenario"],
                "benchmark_dir": exp["benchmark_dir"],
                "expected": {
                    "depth": exp["depth"],
                    "strategy": exp["strategy"],
                    "branches": exp["branches"],
                    "traces": exp["traces"],
                    "bad_harmful": exp["bad_harmful"],
                    "control_harmful": exp["control_harmful"],
                    "historical_cache": {side: None for side in checker.SIDES},
                },
                "classification": checker.INCOMPLETE_EVIDENCE,
                "configuration_dir_present": None,
                "status_records": records,
                "operational": {},
                "provenance": {"present": None, "record": None, "checks": []},
                "sides": {side: {"evidence_present": None} for side in checker.SIDES},
                "issues": [{
                    "category": checker.INCOMPLETE_EVIDENCE,
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
        for side in checker.SIDES
        if config_report["sides"].get(side, {}).get("valid_evidence")
    )
    success = all(config_report["classification"] == checker.SCIENTIFIC_MATCH for config_report in configurations)
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matrix_root": str(matrix_root),
        "repo_root": str(repo_root),
        "expectations": {
            "synthetic_tsv": SYNTHETIC_TSV_RELATIVE.as_posix(),
            "historical_logs_dir": HISTORICAL_LOGS_RELATIVE.as_posix(),
            "historical_logs_found": historical_logs_found,
            "strategy": checker.EXPECTED_STRATEGY,
            "total_configurations": len(configurations),
        },
        "timing_policy": checker.TIMING_POLICY,
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
    for side in checker.SIDES:
        science = config_report["sides"].get(side, {}).get("science")
        if science and science.get("traces") is not None:
            parts.append(f"{side}: traces={science['traces']} harmful={science.get('harmful')}")
        else:
            parts.append(f"{side}: no evidence")
    return "; ".join(parts)


def render_human(report):
    out = []
    out.append("RaceLoom-Bench supplementary S1-S4 scientific checker")
    out.append(f"schema: {SCHEMA}")
    out.append(f"matrix root: {report['matrix_root']}")
    out.append(f"repository:  {report['repo_root']}")
    expectations_meta = report["expectations"]
    out.append(
        f"expectations: {expectations_meta['synthetic_tsv']} "
        f"({expectations_meta['total_configurations']} configurations), "
        f"{expectations_meta['historical_logs_dir']} "
        f"({expectations_meta['historical_logs_found']} historical logs)"
    )
    out.append(f"timing policy: {report['timing_policy']}")
    out.append("")
    out.append("per-configuration results:")
    for config_report in report["configurations"]:
        out.append(
            f"  {config_report['config_id']:<44} "
            f"{config_report['classification']:<22} {science_summary(config_report)}"
        )
    nonmatching = [c for c in report["configurations"] if c["classification"] != checker.SCIENTIFIC_MATCH]
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
    for classification in checker.ALL_CLASSIFICATIONS:
        out.append(f"  {classification}: {counts.get(classification, 0)}")
    out.append(
        f"  sides with valid evidence: "
        f"{report['overall']['sides_with_valid_evidence']}/{report['overall']['sides_total']}"
    )
    matched = counts.get(checker.SCIENTIFIC_MATCH, 0)
    if report["overall"]["success"]:
        out.append("OVERALL: PASS - all 4 supplementary configurations scientifically matched")
    else:
        out.append(
            f"OVERALL: FAIL - {matched}/{report['overall']['total_configurations']} "
            "supplementary configurations scientifically matched"
        )
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_supplementary_matrix.py",
        description="Read-only scientific result checker for the supplementary RaceLoom-Bench S1-S4 group.",
    )
    parser.add_argument(
        "--matrix-root",
        required=True,
        help="existing output root produced by scripts/run_supplementary_matrix.sh",
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
        expectations, order = load_synthetic_tsv(repo_root)
    except ExpectationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    status_path = matrix_root / checker.STATUS_TSV_NAME
    status_present = status_path.is_file()
    status_records = []
    status_warnings = []
    if status_present:
        status_records, status_issues, header_ok = checker.parse_status_tsv(status_path)
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
