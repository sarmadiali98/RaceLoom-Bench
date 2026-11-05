#!/usr/bin/env python3
"""Regression tests for scripts/check_supplementary_matrix.py (Increment 43).

All fixtures are synthetic and live in temporary directories outside the
repository. The tests never invoke Docker or RaceLoom; they exercise the
supplementary checker's parsing and classification logic against fixtures
that replicate the supplementary launcher output formats and the S1-S4
expectation sources (docs/synthetic_s1_s4_matrix.tsv schema, historical
logs under docs/validation_logs/synthetic/).
"""

import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_final_matrix as checker
import check_supplementary_matrix as supp
import test_check_final_matrix as base

SYNTHETIC_TSV_TEXT = "\n".join([
    "ID\tScenario\tDepth\tStrategy\tBranch structure\tGenerated traces\tBad harmful races\tControl harmful races\tBad total seconds\tControl total seconds",
    "S1\tMultidomain wrong destination\t5\tbfs\tC1A:3;C2A:3;C1B:3;C2B:3;BSw:13\t363024\t396\t0\t1427.731890576193\t642.8721467598807",
    "S2\tHierarchical extended wrong destination\t4\tbfs\tC1:7;C2:7;CM:2;BSw:15\t38478\t31\t0\t1049.240204293048\t1059.2249279383104",
    "S3\tMulti-slice shared-core isolation\t5\tbfs\tC1:6;C2:6;BSw:13\t363024\t104\t0\t1287.3523482799064\t867.2769452400971",
    "S4\tMulti-region stale reroute\t5\tbfs\tC1:5;C2:6;CM:2;BSw:12\t150533\t18\t0\t955.192787066102\t965.6332723221276",
]) + "\n"

BENCH_DIRS = {
    "S1": "benchmarks/synthetic/final/s1_multidomain_wrong_destination",
    "S2": "benchmarks/synthetic/final/s2_hierarchical_extended_wrong_destination",
    "S3": "benchmarks/synthetic/final/s3_multi_slice_shared_core_isolation",
    "S4": "benchmarks/synthetic/final/s4_multi_region_stale_reroute",
}

PROVENANCE_SCHEMA = "raceloom-matrix-provenance-v1"
GIT_HEAD = "a" * 40
IMAGE_ID = "sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087"


def synthetic_historical_log_text(s_id, side, depth, traces, harmful, branches, cache):
    exit_key = "BAD_EXIT_CODE" if side == "bad" else "CONTROL_EXIT_CODE"
    parts = [
        "# Validation log",
        "set=synthetic",
        f"id={s_id}",
        "family_or_scenario=synthetic fixture",
        f"side={side}",
        f"depth={depth}",
        f"expected_traces={traces}",
        f"expected_harmful={harmful}",
        "expected_total_seconds=1427.731890576193",
        "",
        "----- BEGIN SANITIZED RACELOOM LOG -----",
        "Model: synthetic/model.json",
        "Args: --depth 5 --strategy bfs",
        "",
        "========== Final Stats ==========",
        "Date: 2026-05-24;20:27:21",
        "SDN model file: model.json",
        "Forwarding properties file: properties.json",
        "Trace generation strategy: bfs",
        f"Depth: {depth}",
        f"Network model branches: {branches}",
        "Trace(s) generation time: 12.381033284007572",
        "Maude execution time: 2.7701479155221023",
        f"Trace generation cache hits: {cache['gen_cache_hits']}",
        f"Trace generation cache misses: {cache['gen_cache_misses']}",
        f"Generated traces: {traces}",
        "KATch total execution time: 1350.2849128727103",
        f"KATch total cache hits: {cache['katch_cache_hits']}",
        f"KATch total cache misses: {cache['katch_cache_misses']}",
        f"Harmful races found: {harmful}",
        "Trace Analyzer execution time: 1377.812679554976",
        "Total execution time: 1427.731890576193",
        "=================================",
        "Output written to: <RACELOOM_WORKDIR>/output/run_2026_05_24T20_27_21",
        "",
        "RaceLoom finished with exit code: 0",
        f"{exit_key}=0",
        "",
        "----- END SANITIZED RACELOOM LOG -----",
        "",
    ]
    return "\n".join(parts)


class Fixture:
    def __init__(self, root):
        self.root = Path(root)
        self.repo = self.root / "repo"
        self.matrix = self.root / "matrix"
        self.repo.mkdir(parents=True)
        self.matrix.mkdir(parents=True)
        docs = self.repo / "docs"
        docs.mkdir()
        (docs / "synthetic_s1_s4_matrix.tsv").write_text(SYNTHETIC_TSV_TEXT, encoding="utf-8")
        (docs / "validation_logs" / "synthetic").mkdir(parents=True)
        (self.repo / "benchmarks" / "synthetic" / "final").mkdir(parents=True)
        for config_id in BENCH_DIRS:
            self.ensure_inputs(config_id)
        self.expectations, self.order = supp.load_synthetic_tsv(self.repo)
        self.status_records = []
        self.status_override = None

    def exp(self, config_id):
        return dict(self.expectations[config_id])

    def s_id(self, config_id):
        return self.expectations[config_id]["s_id"]

    def cache(self, config_id, side):
        index = self.order.index(config_id)
        offset = 0 if side == "bad" else 1
        return {
            "gen_cache_hits": 20000 + index * 11 + offset,
            "gen_cache_misses": 1400 + index + offset,
            "katch_cache_hits": 1000000 + index * 17 + offset,
            "katch_cache_misses": 1500 + index + offset,
        }

    def input_hash(self, config_id, side, name):
        path = self.repo / self.exp(config_id)["benchmark_dir"] / side / name
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def ensure_inputs(self, config_id):
        bench = self.repo / BENCH_DIRS[config_id.split("_", 1)[0]]
        for side in ("bad", "control"):
            for name in ("model.json", "properties.json"):
                path = bench / side / name
                if not path.is_file():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(f"synthetic {config_id} {side} {name}\n", encoding="utf-8")

    def write_historical_logs(self, config_id):
        exp = self.exp(config_id)
        for side in ("bad", "control"):
            harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
            text = synthetic_historical_log_text(
                exp["s_id"], side, exp["depth"], exp["traces"], harmful,
                exp["branches"], self.cache(config_id, side),
            )
            path = self.repo / "docs" / "validation_logs" / "synthetic" / f"{exp['s_id']}_{side}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def provenance_text(self, config_id, overrides=None):
        exp = self.exp(config_id)
        bench = exp["benchmark_dir"]
        cfg_dir = f"/matrix-root/{config_id}"
        values = {
            "provenance_schema": PROVENANCE_SCHEMA,
            "config_id": config_id,
            "benchmark": bench,
            "depth": str(exp["depth"]),
            "strategy": "bfs",
            "execution_order": "bad_then_control",
            "bad_model_path": f"/repo/{bench}/bad/model.json",
            "bad_properties_path": f"/repo/{bench}/bad/properties.json",
            "control_model_path": f"/repo/{bench}/control/model.json",
            "control_properties_path": f"/repo/{bench}/control/properties.json",
            "sha256_bad_model": self.input_hash(config_id, "bad", "model.json"),
            "sha256_bad_properties": self.input_hash(config_id, "bad", "properties.json"),
            "sha256_control_model": self.input_hash(config_id, "control", "model.json"),
            "sha256_control_properties": self.input_hash(config_id, "control", "properties.json"),
            "sha256_tool": "sha256sum",
            "requested_image": "raceloom:latest",
            "resolved_image_id": IMAGE_ID,
            "image_architecture": "x86_64",
            "image_repo_digest": "not_available",
            "sha256_run_one_pair_sh": hashlib.sha256(b"run_one_pair").hexdigest(),
            "sha256_run_raceloom_progress_sh": hashlib.sha256(b"wrapper").hexdigest(),
            "sha256_run_final_matrix_sh": hashlib.sha256(b"supplementary-launcher").hexdigest(),
            "note_sha256_run_final_matrix_sh": "hash of the executing supplementary launcher script itself",
            "git_branch": "fix/reviewer-reproducibility",
            "git_head": GIT_HEAD,
            "git_worktree_state": "dirty",
            "wt_fingerprint": hashlib.sha256(f"wtfp-{config_id}".encode()).hexdigest(),
            "wt_fingerprint_algorithm": "sha256 of a manifest of all tracked and untracked files",
            "wt_fingerprint_utc": "2026-11-04T18:00:00Z",
            "wt_tracked_files": "100",
            "wt_untracked_nonignored_files": "7",
            "pair_runner_command": f"RACELOOM_OUTPUT_DIR={cfg_dir}/artifacts scripts/run_one_pair.sh {bench} {exp['depth']} {cfg_dir}/console",
            "pair_runner_arg_bench": bench,
            "pair_runner_arg_depth": str(exp["depth"]),
            "pair_runner_arg_out_dir": f"{cfg_dir}/console",
            "pair_runner_env_RACELOOM_OUTPUT_DIR": f"{cfg_dir}/artifacts",
            "console_dir": f"{cfg_dir}/console",
            "artifacts_base_dir": f"{cfg_dir}/artifacts",
            "utc_prepared": "2026-11-04T18:00:00Z",
            "utc_prepared_note": "provenance creation time in UTC before pair execution",
            "host_hostname": "fixture-host",
            "host_architecture": "x86_64",
            "docker_client_version": "29.1.3",
            "docker_server_version": "29.1.3",
            "host_python3_version": "3.14.4",
            "runtime_python_version": "not_recorded",
            "runtime_python_version_note": "intentionally not queried",
        }
        if overrides:
            values.update(overrides)
        return "".join(f"{key}={value}\n" for key, value in values.items())

    def write_config(self, config_id, *, status="COMPLETE", exit_code="0",
                     complete_marker=True, in_progress_marker=False,
                     provenance=True, provenance_overrides=None,
                     sides=None, extra_records=None, detail=None):
        exp = self.exp(config_id)
        depth = exp["depth"]
        cfg_dir = self.matrix / config_id
        (cfg_dir / "console").mkdir(parents=True, exist_ok=True)
        (cfg_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        self.ensure_inputs(config_id)
        self.write_historical_logs(config_id)
        sides = sides or {}

        if provenance:
            text = self.provenance_text(config_id, overrides=provenance_overrides)
            (cfg_dir / "provenance.tsv").write_text(text, encoding="utf-8")

        if complete_marker:
            marker = "\n".join([
                f"config_id={config_id}",
                f"benchmark={exp['benchmark_dir']}",
                f"depth={depth}",
                f"exit_code={exit_code}",
                "utc_start=2026-11-04T18:00:00Z",
                "utc_end=2026-11-04T18:30:00Z",
                f"evidence_dir={cfg_dir}",
            ]) + "\n"
            (cfg_dir / "STATUS_COMPLETE").write_text(marker, encoding="utf-8")
        if in_progress_marker:
            marker = "\n".join([
                f"config_id={config_id}",
                f"benchmark={exp['benchmark_dir']}",
                f"depth={depth}",
                "utc_start=2026-11-04T18:00:00Z",
                "pid=12345",
            ]) + "\n"
            (cfg_dir / "STATUS_IN_PROGRESS").write_text(marker, encoding="utf-8")

        for side in ("bad", "control"):
            opts = dict(sides.get(side) or {})
            harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
            cache = self.cache(config_id, side)
            console_path = cfg_dir / "console" / f"{exp['log_base']}_{side}_depth{depth}.log"
            csv_path = cfg_dir / "artifacts" / side / "final_stats.csv"
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            console = opts.get("console", "default")
            if console is None:
                pass
            elif console == "":
                console_path.write_text("", encoding="utf-8")
            elif console == "default":
                console_path.write_text(
                    base.console_log_text(depth, exp["strategy"], exp["branches"], exp["traces"], harmful, cache),
                    encoding="utf-8")
            else:
                console_path.write_text(console, encoding="utf-8")

            csv = opts.get("csv", "default")
            if csv is None:
                pass
            elif csv == "":
                csv_path.write_text("", encoding="utf-8")
            elif csv == "default":
                csv_path.write_text(
                    base.final_stats_csv_text(depth, exp["strategy"], exp["branches"], exp["traces"], harmful, cache,
                                              overrides=opts.get("csv_overrides")),
                    encoding="utf-8")
            else:
                csv_path.write_text(csv, encoding="utf-8")

            run_dir = cfg_dir / "artifacts" / side / "run_2026_05_24T20_27_21"
            if opts.get("run_dirs", True):
                (run_dir / "harmful_traces").mkdir(parents=True, exist_ok=True)
                (run_dir / "harmful_traces_raw").mkdir(parents=True, exist_ok=True)
                trace_count = opts.get("harmful_trace_files")
                if trace_count is None:
                    trace_count = 1 if harmful > 0 else 0
                for i in range(trace_count):
                    (run_dir / "harmful_traces" / f"harmful_trace_{i}.gv").write_text(f"trace {i}\n", encoding="utf-8")
                    (run_dir / "harmful_traces_raw" / f"harmful_trace_raw_{i}.txt").write_text(f"raw {i}\n", encoding="utf-8")

        if status is not None:
            record = {
                "config_id": config_id,
                "benchmark": exp["benchmark_dir"],
                "depth": str(depth),
                "status": status,
                "exit_code": exit_code,
                "utc_start": "2026-11-04T18:00:00Z",
                "utc_end": "2026-11-04T18:30:00Z",
                "evidence_dir": str(cfg_dir),
                "detail": detail if detail is not None else "pair runner exited 0 with preserved minimum evidence and provenance; not scientifically validated",
            }
            self.status_records.append(record)
            for extra in extra_records or []:
                self.status_records.append(extra)

    def write_status(self):
        path = self.matrix / "status.tsv"
        if self.status_override is not None:
            path.write_text(self.status_override, encoding="utf-8")
            return
        lines = ["\t".join(checker.STATUS_HEADER)]
        for record in self.status_records:
            lines.append("\t".join(record[column] for column in checker.STATUS_HEADER))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_check(self, extra_args=None, json_mode=False):
        self.write_status()
        args = ["--matrix-root", str(self.matrix), "--repo-root", str(self.repo)]
        if json_mode:
            args.append("--json")
        if extra_args:
            args.extend(extra_args)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = supp.main(args)
        return code, buffer.getvalue()

    def run_report(self, extra_args=None):
        code, out = self.run_check(extra_args=extra_args, json_mode=True)
        return code, json.loads(out)

    def config_report(self, report, config_id):
        for entry in report["configurations"]:
            if entry["config_id"] == config_id:
                return entry
        raise AssertionError(f"configuration {config_id} missing from report")

    def tree_snapshot(self):
        snapshot = {}
        for base_dir in (self.repo, self.matrix):
            for path in sorted(base_dir.rglob("*")):
                if path.is_file():
                    snapshot[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                elif path.is_dir():
                    snapshot[str(path)] = "dir"
        return snapshot


class CheckSupplementaryMatrixTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="raceloom-supp-tests-")
        self.fixture = Fixture(self._tmp)
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def write_all_valid(self):
        for config_id in self.fixture.order:
            self.fixture.write_config(config_id)

    def assert_classification(self, config_id, expected):
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        entry = self.fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], expected, msg=json.dumps(entry["issues"], indent=2))
        return entry

    def branches_comparison(self, entry, side):
        comparisons = [c for c in entry["sides"][side]["comparisons"] if c["field"] == "branches"]
        self.assertEqual(len(comparisons), 1)
        return comparisons[0]

    def rewrite_branch_order(self, config_id, branches):
        fixture = self.fixture
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        for side in ("bad", "control"):
            harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
            cache = fixture.cache(config_id, side)
            console_path = cfg_dir / "console" / f"{exp['log_base']}_{side}_depth{exp['depth']}.log"
            console_path.write_text(
                base.console_log_text(exp["depth"], exp["strategy"], branches, exp["traces"], harmful, cache),
                encoding="utf-8")
            csv_path = cfg_dir / "artifacts" / side / "final_stats.csv"
            csv_path.write_text(
                base.final_stats_csv_text(exp["depth"], exp["strategy"], branches, exp["traces"], harmful, cache),
                encoding="utf-8")

    def test_synthetic_tsv_parses_with_real_schema(self):
        expectations, order = supp.load_synthetic_tsv(self.fixture.repo)
        self.assertEqual(order, [
            "S1_multidomain_wrong_destination",
            "S2_hierarchical_extended_wrong_destination",
            "S3_multi_slice_shared_core_isolation",
            "S4_multi_region_stale_reroute",
        ])
        s1 = expectations["S1_multidomain_wrong_destination"]
        self.assertEqual(s1["s_id"], "S1")
        self.assertEqual(s1["depth"], 5)
        self.assertEqual(s1["strategy"], "bfs")
        self.assertEqual(s1["traces"], 363024)
        self.assertEqual(s1["bad_harmful"], 396)
        self.assertEqual(s1["control_harmful"], 0)
        self.assertEqual(s1["branches"], "C1A:3;C2A:3;C1B:3;C2B:3;BSw:13")
        s2 = expectations["S2_hierarchical_extended_wrong_destination"]
        self.assertEqual(s2["depth"], 4)
        self.assertEqual(s2["traces"], 38478)
        self.assertEqual(s2["bad_harmful"], 31)

    def test_expected_config_count_is_4(self):
        self.assertEqual(supp.EXPECTED_CONFIG_COUNT, 4)
        _, order = supp.load_synthetic_tsv(self.fixture.repo)
        self.assertEqual(len(order), 4)
        self.assertEqual(len(set(order)), 4)

    def test_all_matching_group_passes(self):
        self.write_all_valid()
        code, report = self.fixture.run_report()
        self.assertEqual(code, 0)
        self.assertTrue(report["overall"]["success"])
        self.assertEqual(report["overall"]["total_configurations"], 4)
        self.assertEqual(report["overall"]["classification_counts"], {"SCIENTIFIC_MATCH": 4})
        self.assertEqual(report["overall"]["sides_with_valid_evidence"], 8)

    def test_valid_pair_is_scientific_match(self):
        self.fixture.write_config("S1_multidomain_wrong_destination")
        entry = self.assert_classification("S1_multidomain_wrong_destination", "SCIENTIFIC_MATCH")
        self.assertTrue(entry["sides"]["bad"]["valid_evidence"])
        self.assertTrue(entry["sides"]["control"]["valid_evidence"])

    def test_reordered_branch_signature_is_scientific_match(self):
        config_id = "S1_multidomain_wrong_destination"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "C2A:3;C1A:3;C2B:3;C1B:3;BSw:13")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)  # 3 configurations remain NOT_RUN
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "match")
        self.assertEqual(comparison["expected"], "C1A:3;C2A:3;C1B:3;C2B:3;BSw:13")
        self.assertEqual(comparison["actual"], "C2A:3;C1A:3;C2B:3;C1B:3;BSw:13")
        self.assertEqual(comparison["expected_branch_counts"], comparison["actual_branch_counts"])

    def test_reordered_signatures_across_full_group_still_pass(self):
        fixture = self.fixture
        self.write_all_valid()
        self.rewrite_branch_order("S1_multidomain_wrong_destination", "C2A:3;C1A:3;C2B:3;C1B:3;BSw:13")
        self.rewrite_branch_order("S2_hierarchical_extended_wrong_destination", "C2:7;C1:7;CM:2;BSw:15")
        code, report = fixture.run_report()
        self.assertEqual(code, 0)
        self.assertTrue(report["overall"]["success"])
        self.assertEqual(report["overall"]["classification_counts"], {"SCIENTIFIC_MATCH": 4})
        self.assertEqual(report["overall"]["sides_with_valid_evidence"], 8)

    def test_different_branch_count_is_mismatch(self):
        config_id = "S3_multi_slice_shared_core_isolation"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "C2:6;C1:7;BSw:13")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "mismatch")
        self.assertIn("C1 expected 6 actual 7", comparison["detail"])

    def test_malformed_actual_branch_signature_is_mismatch(self):
        config_id = "S1_multidomain_wrong_destination"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "C1A:3;C2A:3;C1B:3;C2B:3;BSw")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "malformed_actual")

    def test_duplicate_branch_names_are_rejected(self):
        config_id = "S1_multidomain_wrong_destination"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "C1A:3;C1A:3;C1B:3;C2B:3;BSw:13")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "malformed_actual")
        self.assertIn("duplicate branch name 'C1A'", comparison["detail"])

    def test_wrong_harmful_count_is_mismatch(self):
        config_id = "S4_multi_region_stale_reroute"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            base.console_log_text(exp["depth"], exp["strategy"], exp["branches"], exp["traces"], 17, cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            base.final_stats_csv_text(exp["depth"], exp["strategy"], exp["branches"], exp["traces"], 17, cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        harmful = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "harmful"]
        self.assertEqual(harmful[0]["outcome"], "mismatch")
        self.assertEqual(harmful[0]["actual"], 17)

    def test_wrong_trace_count_is_mismatch(self):
        config_id = "S2_hierarchical_extended_wrong_destination"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"control": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "control")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_control_depth{exp['depth']}.log"
        console_path.write_text(
            base.console_log_text(exp["depth"], exp["strategy"], exp["branches"], 38477, exp["control_harmful"], cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "control" / "final_stats.csv"
        csv_path.write_text(
            base.final_stats_csv_text(exp["depth"], exp["strategy"], exp["branches"], 38477, exp["control_harmful"], cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        traces = [c for c in entry["sides"]["control"]["comparisons"] if c["field"] == "traces"]
        self.assertEqual(traces[0]["outcome"], "mismatch")
        self.assertEqual(traces[0]["actual"], 38477)

    def test_historical_cache_mismatch_is_scientific_mismatch(self):
        config_id = "S1_multidomain_wrong_destination"
        fixture = self.fixture
        cache = dict(fixture.cache(config_id, "bad"))
        cache["katch_cache_hits"] += 1
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            base.console_log_text(exp["depth"], exp["strategy"], exp["branches"], exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            base.final_stats_csv_text(exp["depth"], exp["strategy"], exp["branches"], exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        katch = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "katch_cache_hits"]
        self.assertEqual(katch[0]["outcome"], "mismatch")
        self.assertEqual(katch[0]["source"], "historical_log")

    def test_missing_historical_log_is_reported_unavailable(self):
        config_id = "S1_multidomain_wrong_destination"
        self.fixture.write_config(config_id)
        log_dir = self.fixture.repo / "docs" / "validation_logs" / "synthetic"
        (log_dir / "S1_control.txt").unlink()
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        entry = self.fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        self.assertIsNone(entry["expected"]["historical_cache"]["control"])
        comparisons = entry["sides"]["control"]["comparisons"]
        self.assertTrue(any(c["outcome"] == "unavailable" and c["source"] == "historical_log" for c in comparisons))

    def test_wrong_model_sha256_is_provenance_mismatch(self):
        self.fixture.write_config("S2_hierarchical_extended_wrong_destination",
                                  provenance_overrides={"sha256_bad_model": "0" * 64})
        entry = self.assert_classification("S2_hierarchical_extended_wrong_destination", "PROVENANCE_MISMATCH")
        checks = {c["check"]: c for c in entry["provenance"]["checks"]}
        self.assertEqual(checks["sha256_bad_model"]["outcome"], "mismatch")

    def test_missing_configuration_is_not_run(self):
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        entry = self.fixture.config_report(report, "S1_multidomain_wrong_destination")
        self.assertEqual(entry["classification"], "NOT_RUN")
        self.assertFalse(entry["configuration_dir_present"])

    def test_failed_status_is_infrastructure_failure(self):
        self.fixture.write_config("S4_multi_region_stale_reroute", status="FAILED", exit_code="2", detail="pair runner failed")
        entry = self.assert_classification("S4_multi_region_stale_reroute", "INFRASTRUCTURE_FAILURE")
        self.assertEqual(entry["operational"]["last_status"], "FAILED")

    def test_interrupted_run_is_not_complete(self):
        self.fixture.write_config("S3_multi_slice_shared_core_isolation", in_progress_marker=True)
        entry = self.assert_classification("S3_multi_slice_shared_core_isolation", "INCOMPLETE_EVIDENCE")
        self.assertTrue(any("STATUS_IN_PROGRESS" in issue["detail"] for issue in entry["issues"]))

    def test_malformed_synthetic_tsv_is_environment_error(self):
        fixture = self.fixture
        tsv = fixture.repo / "docs" / "synthetic_s1_s4_matrix.tsv"
        lines = tsv.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1].replace("\t363024\t396\t0\t", "\tnot-a-number\t396\t0\t")
        tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fixture.write_config("S1_multidomain_wrong_destination")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_missing_synthetic_tsv_is_environment_error(self):
        fixture = self.fixture
        (fixture.repo / "docs" / "synthetic_s1_s4_matrix.tsv").unlink()
        fixture.write_config("S1_multidomain_wrong_destination")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_non_bfs_strategy_in_tsv_is_environment_error(self):
        fixture = self.fixture
        tsv = fixture.repo / "docs" / "synthetic_s1_s4_matrix.tsv"
        lines = tsv.read_text(encoding="utf-8").splitlines()
        lines[2] = lines[2].replace("\tbfs\t", "\tdfs\t")
        tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fixture.write_config("S1_multidomain_wrong_destination")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_checker_does_not_modify_any_files(self):
        self.write_all_valid()
        self.fixture.write_status()
        before = self.fixture.tree_snapshot()
        self.fixture.run_check()
        self.fixture.run_check(json_mode=True)
        after = self.fixture.tree_snapshot()
        self.assertEqual(before, after)

    def test_json_output_is_parseable_and_stable(self):
        self.write_all_valid()
        code1, out1 = self.fixture.run_check(json_mode=True)
        code2, out2 = self.fixture.run_check(json_mode=True)
        self.assertEqual(code1, code2)
        report1 = json.loads(out1)
        report2 = json.loads(out2)
        self.assertEqual(report1["schema"], "raceloom-supplementary-check-report-v1")
        report1.pop("generated_utc")
        report2.pop("generated_utc")
        self.assertEqual(report1, report2)

    def test_human_output_pass_line_for_full_group(self):
        self.write_all_valid()
        code, out = self.fixture.run_check()
        self.assertEqual(code, 0)
        self.assertIn("OVERALL: PASS - all 4 supplementary configurations scientifically matched", out)

    def test_provenance_launcher_hash_key_maps_to_supplementary_script(self):
        self.assertEqual(
            checker.PROVENANCE_SCRIPT_FILES["sha256_run_final_matrix_sh"],
            "scripts/run_supplementary_matrix.sh")


if __name__ == "__main__":
    unittest.main(verbosity=2)
