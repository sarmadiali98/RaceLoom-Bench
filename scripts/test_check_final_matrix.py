#!/usr/bin/env python3
"""Regression tests for scripts/check_final_matrix.py.

All fixtures are synthetic and live in temporary directories outside the
repository. The tests never invoke Docker or RaceLoom; they exercise only the
checker's pure file-parsing and classification logic against fixtures that
replicate the verified matrix launcher output formats (status.tsv, completion
markers, provenance.tsv key=value records, console logs with Final Stats
blocks, side-root final_stats.csv files and persisted run_* directories).
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

MATRIX_TSV_TEXT = "\n".join([
    "benchmark\ttopology\tk\tdepth\tbranches\ttraces\tbad_harmful\tcontrol_harmful",
    "B1_waypoint_order\tT1_atlanta\tK8\t5\tCBg:8;CIngress:1;CWaypoint:1;BSw:11\t156100\t62\t0",
    "B1_waypoint_order\tT2_nobel_eu\tK12\t4\tCBg:12;CIngress:1;CWaypoint:1;BSw:15\t49980\t38\t0",
    "B1_waypoint_order\tT3_geant2012\tK14\t4\tCBg:14;CIngress:1;CWaypoint:1;BSw:17\t82688\t44\t0",
    "B1_waypoint_order\tT4_germany50\tK16\t4\tCBg:16;CIngress:1;CWaypoint:1;BSw:19\t129276\t50\t0",
    "B2_route_mapping\tT1_atlanta\tK8\t5\tCBg:8;CRoute:1;BSw:10\t96309\t74\t0",
    "B2_route_mapping\tT2_nobel_eu\tK12\t4\tCBg:12;CRoute:1;BSw:14\t37856\t25\t0",
    "B2_route_mapping\tT3_geant2012\tK14\t4\tCBg:14;CRoute:1;BSw:16\t64800\t29\t0",
    "B2_route_mapping\tT4_germany50\tK16\t4\tCBg:16;CRoute:1;BSw:18\t104040\t33\t0",
    "B3_slice_isolation\tT1_atlanta\tK8\t5\tCBg:8;CSliceA:1;CSliceB:1;BSw:11\t156100\t72\t0",
    "B3_slice_isolation\tT2_nobel_eu\tK12\t4\tCBg:12;CSliceA:1;CSliceB:1;BSw:15\t49980\t51\t0",
    "B3_slice_isolation\tT3_geant2012\tK14\t4\tCBg:14;CSliceA:1;CSliceB:1;BSw:17\t82688\t46\t0",
    "B3_slice_isolation\tT4_germany50\tK16\t4\tCBg:16;CSliceA:1;CSliceB:1;BSw:19\t129276\t67\t0",
    "B4_failover_cleanup\tT1_atlanta\tK8\t5\tCBg:8;CDetect:1;CFailover:1;CCleanup:1;BSw:12\t242363\t79\t0",
    "B4_failover_cleanup\tT2_nobel_eu\tK12\t4\tCBg:12;CDetect:1;CFailover:1;CCleanup:1;BSw:16\t64800\t51\t0",
    "B4_failover_cleanup\tT3_geant2012\tK14\t4\tCBg:14;CDetect:1;CFailover:1;CCleanup:1;BSw:18\t104040\t59\t0",
    "B4_failover_cleanup\tT4_germany50\tK16\t4\tCBg:16;CDetect:1;CFailover:1;CCleanup:1;BSw:20\t158840\t67\t0",
]) + "\n"

FAMILY_DIRS = {
    "B1": "b1_waypoint_order_churn",
    "B2": "b2_route_mapping_forced_distinct",
    "B3": "b3_slice_isolation_twocontroller_churn",
    "B4": "b4_failover_cleanup_churn",
}

PROVENANCE_SCHEMA = "raceloom-matrix-provenance-v1"
GIT_HEAD = "a" * 40
IMAGE_ID = "sha256:fe13627b75f8e7c8c3d2299a1090f2eeac255785b4a569ad5b84766180e24087"

DEFAULT_TIMINGS = {
    "gen": "4.125612827949226",
    "maude": "0.5955197440925986",
    "katch": "552.2770894817077",
    "analyzer": "559.4097988121212",
    "total": "563.5354116400704",
}


def console_log_text(depth, strategy, branches, traces, harmful, cache, timings=None):
    timings = timings or DEFAULT_TIMINGS
    parts = [
        "Generating traces...",
        "",
        "Date: 2026-06-02;11:27:53",
        "SDN model file: model.json",
        "Forwarding properties file: properties.json",
        f"Trace generation strategy: {strategy}",
        f"Depth: {depth}",
        f"Network model branches: {branches}",
        f"Trace(s) generation time: {timings['gen']}",
        f"Maude execution time: {timings['maude']}",
        f"Trace generation cache hits: {cache['gen_cache_hits']}",
        f"Trace generation cache misses: {cache['gen_cache_misses']}",
        f"Generated traces: {traces}",
        "",
        "Analyzing traces...",
        "",
        "========== Final Stats ==========",
        "Date: 2026-06-02;11:27:53",
        "SDN model file: model.json",
        "Forwarding properties file: properties.json",
        f"Trace generation strategy: {strategy}",
        f"Depth: {depth}",
        f"Network model branches: {branches}",
        f"Trace(s) generation time: {timings['gen']}",
        f"Maude execution time: {timings['maude']}",
        f"Trace generation cache hits: {cache['gen_cache_hits']}",
        f"Trace generation cache misses: {cache['gen_cache_misses']}",
        f"Generated traces: {traces}",
        f"KATch total execution time: {timings['katch']}",
        f"KATch total cache hits: {cache['katch_cache_hits']}",
        f"KATch total cache misses: {cache['katch_cache_misses']}",
        f"Harmful races found: {harmful}",
        f"Trace Analyzer execution time: {timings['analyzer']}",
        f"Total execution time: {timings['total']}",
        "=================================",
        "Output written to: /raceloom/output/run_2026_06_02T11_27_53",
        "",
    ]
    return "\n".join(parts)


def final_stats_csv_text(depth, strategy, branches, traces, harmful, cache, timings=None, overrides=None):
    timings = timings or DEFAULT_TIMINGS
    values = {
        "date": "2026-06-02;11:27:53",
        "sdnModelFile": "model.json",
        "forwardingPropsFilePath": "properties.json",
        "strategy": strategy,
        "depth": str(depth),
        "modelBranchCounts": branches,
        "tracesGenTime": timings["gen"],
        "maudeExecTime": timings["maude"],
        "traceGenCacheHits": str(cache["gen_cache_hits"]),
        "traceGenCacheMisses": str(cache["gen_cache_misses"]),
        "generatedTraces": str(traces),
        "katchExecTime": timings["katch"],
        "katchCacheHits": str(cache["katch_cache_hits"]),
        "katchCacheMisses": str(cache["katch_cache_misses"]),
        "harmfulRaces": str(harmful),
        "traceAnalyzerExecTime": timings["analyzer"],
        "totalExecTime": timings["total"],
    }
    if overrides:
        values.update(overrides)
    columns = checker.FINAL_STATS_COLUMNS
    return ",".join(columns) + "\n" + ",".join(values[c] for c in columns) + "\n"


def historical_log_text(config_id, side, depth, traces, harmful, branches, cache):
    exit_key = "BAD_EXIT_CODE" if side == "bad" else "CONTROL_EXIT_CODE"
    parts = [
        "# Validation log",
        "set=main",
        f"id={config_id.split('_')[0]}",
        "family_or_scenario=synthetic fixture",
        f"topology_or_case={config_id.split('_')[1]}/{config_id.split('_', 2)[2]}",
        f"side={side}",
        f"depth={depth}",
        f"expected_traces={traces}",
        f"expected_harmful={harmful}",
        "expected_total_seconds=563.5354116400704",
        "",
        "----- BEGIN SANITIZED RACELOOM LOG -----",
        "Model: synthetic/model.json",
        "Args: --depth 5 --strategy bfs",
        "",
        "========== Final Stats ==========",
        "Date: 2026-06-02;11:27:53",
        "SDN model file: model.json",
        "Forwarding properties file: properties.json",
        "Trace generation strategy: bfs",
        f"Depth: {depth}",
        f"Network model branches: {branches}",
        "Trace(s) generation time: 4.125612827949226",
        "Maude execution time: 0.5955197440925986",
        f"Trace generation cache hits: {cache['gen_cache_hits']}",
        f"Trace generation cache misses: {cache['gen_cache_misses']}",
        f"Generated traces: {traces}",
        "KATch total execution time: 552.2770894817077",
        f"KATch total cache hits: {cache['katch_cache_hits']}",
        f"KATch total cache misses: {cache['katch_cache_misses']}",
        f"Harmful races found: {harmful}",
        "Trace Analyzer execution time: 559.4097988121212",
        "Total execution time: 563.5354116400704",
        "=================================",
        "Output written to: <RACELOOM_WORKDIR>/output/run_2026_06_02T11_27_53",
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
        (docs / "final_4x4_matrix.tsv").write_text(MATRIX_TSV_TEXT, encoding="utf-8")
        (docs / "validation_logs" / "main").mkdir(parents=True)
        (self.repo / "benchmarks" / "final").mkdir(parents=True)
        self.expectations, self.order = checker.load_matrix_tsv(self.repo)
        self.status_records = []
        self.status_override = None
        for config_id in self.order:
            self.ensure_inputs(config_id)

    def exp(self, config_id):
        exp = dict(self.expectations[config_id])
        family = FAMILY_DIRS[exp["family_tag"]]
        bench = f"benchmarks/final/{family}/{exp['k']}/{exp['topology']}"
        exp["benchmark_dir"] = bench
        exp["log_base"] = bench.replace("/", "_")
        return exp

    def cache(self, config_id, side):
        index = self.order.index(config_id)
        offset = 0 if side == "bad" else 1
        return {
            "gen_cache_hits": 10000 + index * 7 + offset,
            "gen_cache_misses": 500 + index + offset,
            "katch_cache_hits": 200000 + index * 13 + offset,
            "katch_cache_misses": 600 + index + offset,
        }

    def input_hash(self, config_id, side, name):
        path = self.repo / self.exp(config_id)["benchmark_dir"] / side / name
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def ensure_inputs(self, config_id):
        bench = self.repo / self.exp(config_id)["benchmark_dir"]
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
            text = historical_log_text(
                config_id, side, exp["depth"], exp["traces"], harmful,
                exp["branches"], self.cache(config_id, side),
            )
            path = self.repo / "docs" / "validation_logs" / "main" / f"{config_id}_{side}.txt"
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
            "sha256_tool": "shasum -a 256",
            "requested_image": "raceloom:latest",
            "resolved_image_id": IMAGE_ID,
            "image_architecture": "x86_64",
            "image_repo_digest": "not_available",
            "sha256_run_one_pair_sh": hashlib.sha256(b"run_one_pair").hexdigest(),
            "sha256_run_raceloom_progress_sh": hashlib.sha256(b"wrapper").hexdigest(),
            "sha256_run_final_matrix_sh": hashlib.sha256(b"launcher").hexdigest(),
            "note_sha256_run_final_matrix_sh": "hash of the executing matrix launcher script itself",
            "git_branch": "fix/reviewer-reproducibility",
            "git_head": GIT_HEAD,
            "git_worktree_state": "dirty",
            "wt_fingerprint": hashlib.sha256(f"wtfp-{config_id}".encode()).hexdigest(),
            "wt_fingerprint_algorithm": "sha256 of a manifest of all tracked and untracked files",
            "wt_fingerprint_utc": "2026-11-03T10:00:00Z",
            "wt_tracked_files": "100",
            "wt_untracked_nonignored_files": "5",
            "pair_runner_command": f"RACELOOM_OUTPUT_DIR={cfg_dir}/artifacts scripts/run_one_pair.sh {bench} {exp['depth']} {cfg_dir}/console",
            "pair_runner_arg_bench": bench,
            "pair_runner_arg_depth": str(exp["depth"]),
            "pair_runner_arg_out_dir": f"{cfg_dir}/console",
            "pair_runner_env_RACELOOM_OUTPUT_DIR": f"{cfg_dir}/artifacts",
            "console_dir": f"{cfg_dir}/console",
            "artifacts_base_dir": f"{cfg_dir}/artifacts",
            "utc_prepared": "2026-11-03T10:00:00Z",
            "utc_prepared_note": "provenance creation time in UTC before pair execution",
            "host_hostname": "fixture-host",
            "host_architecture": "x86_64",
            "docker_client_version": "29.1.3",
            "docker_server_version": "29.1.3",
            "host_python3_version": "3.12.0",
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
                "utc_start=2026-11-03T10:00:00Z",
                "utc_end=2026-11-03T10:30:00Z",
                f"evidence_dir={cfg_dir}",
            ]) + "\n"
            (cfg_dir / "STATUS_COMPLETE").write_text(marker, encoding="utf-8")
        if in_progress_marker:
            marker = "\n".join([
                f"config_id={config_id}",
                f"benchmark={exp['benchmark_dir']}",
                f"depth={depth}",
                "utc_start=2026-11-03T10:00:00Z",
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
                    console_log_text(depth, "bfs", exp["branches"], exp["traces"], harmful, cache),
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
                    final_stats_csv_text(depth, "bfs", exp["branches"], exp["traces"], harmful, cache,
                                         overrides=opts.get("csv_overrides")),
                    encoding="utf-8")
            else:
                csv_path.write_text(csv, encoding="utf-8")

            run_dir = cfg_dir / "artifacts" / side / "run_2026_06_02T11_27_53"
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
                "utc_start": "2026-11-03T10:00:00Z",
                "utc_end": "2026-11-03T10:30:00Z",
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
            code = checker.main(args)
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
        for base in (self.repo, self.matrix):
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    snapshot[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                elif path.is_dir():
                    snapshot[str(path)] = "dir"
        return snapshot


class CheckFinalMatrixTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="raceloom-check-tests-")
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

    def test_matrix_tsv_parses_with_real_schema(self):
        expectations, order = checker.load_matrix_tsv(self.fixture.repo)
        self.assertEqual(len(order), 16)
        exp = expectations["B1_K8_T1_atlanta"]
        self.assertEqual(exp["depth"], 5)
        self.assertEqual(exp["traces"], 156100)
        self.assertEqual(exp["bad_harmful"], 62)
        self.assertEqual(exp["control_harmful"], 0)
        self.assertEqual(exp["branches"], "CBg:8;CIngress:1;CWaypoint:1;BSw:11")
        self.assertEqual(exp["k"], "K8")
        self.assertEqual(exp["topology"], "T1_atlanta")

    def test_expected_config_count_is_16(self):
        self.assertEqual(checker.EXPECTED_CONFIG_COUNT, 16)
        _, order = checker.load_matrix_tsv(self.fixture.repo)
        self.assertEqual(len(order), 16)
        self.assertEqual(len(set(order)), 16)

    def test_depth_and_strategy_mapping(self):
        expectations, _ = checker.load_matrix_tsv(self.fixture.repo)
        for config_id, exp in expectations.items():
            expected_depth = 5 if exp["k"] == "K8" else 4
            self.assertEqual(exp["depth"], expected_depth, msg=config_id)
        self.assertEqual(checker.EXPECTED_STRATEGY, "bfs")

    def test_all_matching_matrix_passes(self):
        self.write_all_valid()
        code, report = self.fixture.run_report()
        self.assertEqual(code, 0)
        self.assertTrue(report["overall"]["success"])
        self.assertEqual(report["overall"]["total_configurations"], 16)
        self.assertEqual(report["overall"]["classification_counts"], {"SCIENTIFIC_MATCH": 16})
        self.assertEqual(report["overall"]["sides_with_valid_evidence"], 32)

    def test_valid_pair_is_scientific_match(self):
        self.fixture.write_config("B1_K8_T1_atlanta")
        entry = self.assert_classification("B1_K8_T1_atlanta", "SCIENTIFIC_MATCH")
        self.assertTrue(entry["sides"]["bad"]["valid_evidence"])
        self.assertTrue(entry["sides"]["control"]["valid_evidence"])
        self.assertTrue(entry["sides"]["bad"]["console_csv_consistent"])

    def test_wrong_trace_count_is_scientific_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], 999, exp["bad_harmful"], cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], 999, exp["bad_harmful"], cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        traces = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "traces"]
        self.assertEqual(traces[0]["outcome"], "mismatch")
        self.assertEqual(traces[0]["actual"], 999)
        self.assertEqual(traces[0]["expected"], exp["traces"])

    def test_wrong_harmful_count_is_scientific_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], 61, cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], 61, cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        harmful = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "harmful"]
        self.assertEqual(harmful[0]["actual"], 61)

    def test_wrong_branch_signature_is_scientific_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", "CBg:9;BSw:11", exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", "CBg:9;BSw:11", exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        branches = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "branches"]
        self.assertEqual(branches[0]["actual"], "CBg:9;BSw:11")

    # --- order-independent branch-signature comparison (Increment 42) ---

    def rewrite_branch_order(self, config_id, branches):
        """Rewrite both sides' console and CSV evidence with a new branch order."""
        fixture = self.fixture
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        for side in ("bad", "control"):
            harmful = exp["bad_harmful"] if side == "bad" else exp["control_harmful"]
            cache = fixture.cache(config_id, side)
            console_path = cfg_dir / "console" / f"{exp['log_base']}_{side}_depth{exp['depth']}.log"
            console_path.write_text(
                console_log_text(exp["depth"], "bfs", branches, exp["traces"], harmful, cache),
                encoding="utf-8")
            csv_path = cfg_dir / "artifacts" / side / "final_stats.csv"
            csv_path.write_text(
                final_stats_csv_text(exp["depth"], "bfs", branches, exp["traces"], harmful, cache),
                encoding="utf-8")

    def branches_comparison(self, entry, side):
        comparisons = [c for c in entry["sides"][side]["comparisons"] if c["field"] == "branches"]
        self.assertEqual(len(comparisons), 1)
        return comparisons[0]

    def test_parse_branch_signature_parses_canonical_form(self):
        mapping, error = checker.parse_branch_signature("CBg:14;CIngress:1;CWaypoint:1;BSw:17")
        self.assertIsNone(error)
        self.assertEqual(mapping, {"CBg": 14, "CIngress": 1, "CWaypoint": 1, "BSw": 17})

    def test_parse_branch_signature_maps_are_order_independent(self):
        canonical, canonical_error = checker.parse_branch_signature("CBg:14;CIngress:1;CWaypoint:1;BSw:17")
        reordered, reordered_error = checker.parse_branch_signature("CIngress:1;CWaypoint:1;CBg:14;BSw:17")
        self.assertIsNone(canonical_error)
        self.assertIsNone(reordered_error)
        self.assertEqual(canonical, reordered)

    def test_parse_branch_signature_rejects_malformed_signatures(self):
        malformed = [
            "",
            "   ",
            "CBg",
            "CBg:",
            "CBg:x",
            "CBg:-1",
            "CBg:14;",
            ";CBg:14",
            "CBg:14;;BSw:17",
            "CBg: 14",
            "CBg :14",
            "CBg:14;BSw",
            "CBg:14;BSw:17;CRoute",
        ]
        for bad in malformed:
            mapping, error = checker.parse_branch_signature(bad)
            self.assertIsNone(mapping, msg=f"expected rejection of {bad!r}")
            self.assertTrue(error, msg=f"expected an error reason for {bad!r}")

    def test_parse_branch_signature_rejects_duplicate_branch_names(self):
        for bad in ("CBg:14;CBg:2", "CBg:14;BSw:17;CBg:14", "BSw:17;CBg:1;CBg:1;CRoute:1"):
            mapping, error = checker.parse_branch_signature(bad)
            self.assertIsNone(mapping, msg=f"expected rejection of {bad!r}")
            self.assertIn("duplicate branch name", error, msg=f"expected duplicate-name error for {bad!r}")

    def test_reordered_branch_signature_is_scientific_match(self):
        """Regression for the real B1_K14 incident: identical counts, different order."""
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CWaypoint:1;CBg:14;BSw:17")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)  # 15 configurations remain NOT_RUN
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "match")
        self.assertEqual(comparison["expected"], "CBg:14;CIngress:1;CWaypoint:1;BSw:17")
        self.assertEqual(comparison["actual"], "CIngress:1;CWaypoint:1;CBg:14;BSw:17")
        self.assertEqual(
            comparison["expected_branch_counts"],
            {"CBg": 14, "CIngress": 1, "CWaypoint": 1, "BSw": 17})
        self.assertEqual(comparison["expected_branch_counts"], comparison["actual_branch_counts"])

    def test_reordered_branch_signatures_across_full_matrix_still_pass(self):
        """Both real incidents (B1_K14 and B2_K14) must not break the 16/16 pass."""
        fixture = self.fixture
        self.write_all_valid()
        self.rewrite_branch_order("B1_K14_T3_geant2012", "CIngress:1;CWaypoint:1;CBg:14;BSw:17")
        self.rewrite_branch_order("B2_K14_T3_geant2012", "CRoute:1;CBg:14;BSw:16")
        code, report = fixture.run_report()
        self.assertEqual(code, 0)
        self.assertTrue(report["overall"]["success"])
        self.assertEqual(report["overall"]["classification_counts"], {"SCIENTIFIC_MATCH": 16})
        self.assertEqual(report["overall"]["sides_with_valid_evidence"], 32)
        for config_id, expected_raw, actual_raw in (
            ("B1_K14_T3_geant2012", "CBg:14;CIngress:1;CWaypoint:1;BSw:17", "CIngress:1;CWaypoint:1;CBg:14;BSw:17"),
            ("B2_K14_T3_geant2012", "CBg:14;CRoute:1;BSw:16", "CRoute:1;CBg:14;BSw:16"),
        ):
            entry = fixture.config_report(report, config_id)
            comparison = self.branches_comparison(entry, "bad")
            self.assertEqual(comparison["outcome"], "match", msg=config_id)
            self.assertEqual(comparison["expected"], expected_raw, msg=config_id)
            self.assertEqual(comparison["actual"], actual_raw, msg=config_id)

    def test_reordered_but_different_branch_count_is_mismatch(self):
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CWaypoint:1;CBg:15;BSw:17")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "mismatch")
        self.assertIn("CBg expected 14 actual 15", comparison["detail"])
        self.assertEqual(comparison["actual"], "CIngress:1;CWaypoint:1;CBg:15;BSw:17")

    def test_reordered_signature_with_missing_branch_is_mismatch(self):
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CBg:14;BSw:17")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "mismatch")
        self.assertIn("branch names only in expected: ['CWaypoint']", comparison["detail"])

    def test_reordered_signature_with_extra_branch_is_mismatch(self):
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CWaypoint:1;CBg:14;BSw:17;CGhost:1")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "mismatch")
        self.assertIn("branch names only in actual: ['CGhost']", comparison["detail"])

    def test_malformed_actual_branch_signature_is_mismatch(self):
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CWaypoint:1;CBg:14;BSw")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "malformed_actual")
        self.assertIn("not NAME:COUNT", comparison["detail"])
        self.assertNotIn("actual_branch_counts", comparison)

    def test_duplicate_branch_names_in_actual_signature_are_rejected(self):
        config_id = "B1_K14_T3_geant2012"
        fixture = self.fixture
        fixture.write_config(config_id)
        self.rewrite_branch_order(config_id, "CIngress:1;CWaypoint:1;CBg:14;CBg:2;BSw:17")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        comparison = self.branches_comparison(entry, "bad")
        self.assertEqual(comparison["outcome"], "malformed_actual")
        self.assertIn("duplicate branch name 'CBg'", comparison["detail"])

    def test_malformed_expected_branch_signature_in_tsv_is_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id)
        tsv_path = fixture.repo / "docs" / "final_4x4_matrix.tsv"
        canonical_cell = "CBg:8;CIngress:1;CWaypoint:1;BSw:11"
        cases = [
            ("CBg:8;CIngress", "not NAME:COUNT"),
            ("CBg:8;CBg:8;CIngress:1;CWaypoint:1;BSw:11", "duplicate branch name 'CBg'"),
        ]
        for corrupted, detail_fragment in cases:
            lines = tsv_path.read_text(encoding="utf-8").splitlines()
            target = next(i for i, line in enumerate(lines) if line.startswith("B1_waypoint_order\tT1_atlanta"))
            parts = lines[target].split("\t")
            self.assertEqual(parts[4], canonical_cell)
            parts[4] = corrupted
            lines[target] = "\t".join(parts)
            tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            code, report = fixture.run_report()
            self.assertEqual(code, 1)
            entry = fixture.config_report(report, config_id)
            self.assertEqual(entry["classification"], "SCIENTIFIC_MISMATCH", msg=corrupted)
            comparison = self.branches_comparison(entry, "bad")
            self.assertEqual(comparison["outcome"], "malformed_expected", msg=corrupted)
            self.assertIn(detail_fragment, comparison["detail"], msg=corrupted)
            lines[target] = "\t".join(parts[:4] + [canonical_cell] + parts[5:])
            tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_timing_differences_do_not_fail(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        slow = {"gen": "9.999999999", "maude": "8.888888888", "katch": "777.777777777",
                "analyzer": "776.777777777", "total": "786.777777777"}
        fixture.write_config(config_id, sides={
            "bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                             cache, timings=slow), encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                                 cache, timings=slow), encoding="utf-8")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        self.assertEqual(entry["sides"]["bad"]["csv_timings"]["totalExecTime"], slow["total"])

    def test_extra_timing_precision_does_not_fail(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        precise = {k: "1.2345678901234567890123" for k in DEFAULT_TIMINGS}
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        cache = fixture.cache(config_id, "bad")
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                             cache, timings=precise), encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                                 cache, timings=precise), encoding="utf-8")
        code, report = fixture.run_report()
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))

    def test_missing_final_stats_csv_is_incomplete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", sides={"bad": {"csv": None}})
        entry = self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")
        self.assertFalse(entry["sides"]["bad"]["csv_present"])

    def test_empty_final_stats_csv_is_incomplete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", sides={"bad": {"csv": ""}})
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_missing_console_log_is_incomplete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", sides={"bad": {"console": None}})
        entry = self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")
        self.assertFalse(entry["sides"]["bad"]["console_present"])

    def test_empty_console_log_is_incomplete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", sides={"bad": {"console": ""}})
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_console_csv_conflict_is_rejected(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"csv_overrides": {"generatedTraces": "999"}}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                             fixture.cache(config_id, "bad")), encoding="utf-8")
        entry = self.assert_classification(config_id, "INCOMPLETE_EVIDENCE")
        self.assertFalse(entry["sides"]["bad"]["console_csv_consistent"])
        self.assertFalse(entry["sides"]["bad"]["valid_evidence"])

    def test_missing_complete_marker_is_not_accepted(self):
        self.fixture.write_config("B1_K8_T1_atlanta", complete_marker=False)
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_failed_status_is_infrastructure_failure(self):
        self.fixture.write_config("B1_K8_T1_atlanta", status="FAILED", exit_code="2", detail="pair runner failed")
        entry = self.assert_classification("B1_K8_T1_atlanta", "INFRASTRUCTURE_FAILURE")
        self.assertEqual(entry["operational"]["last_status"], "FAILED")

    def test_interrupted_run_is_not_complete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", in_progress_marker=True)
        entry = self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")
        self.assertTrue(any("STATUS_IN_PROGRESS" in issue["detail"] for issue in entry["issues"]))

    def test_blocked_status_is_incomplete_evidence(self):
        self.fixture.write_config("B1_K8_T1_atlanta", status="BLOCKED", exit_code="-",
                                  detail="existing incomplete evidence; manual recovery required")
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_missing_configuration_is_not_run(self):
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        entry = self.fixture.config_report(report, "B1_K8_T1_atlanta")
        self.assertEqual(entry["classification"], "NOT_RUN")
        self.assertFalse(entry["configuration_dir_present"])

    def test_missing_provenance_is_detected(self):
        self.fixture.write_config("B1_K8_T1_atlanta", provenance=False)
        entry = self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")
        self.assertFalse(entry["provenance"]["present"])

    def test_wrong_model_sha256_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta",
                                  provenance_overrides={"sha256_bad_model": "0" * 64})
        entry = self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")
        checks = {c["check"]: c for c in entry["provenance"]["checks"]}
        self.assertEqual(checks["sha256_bad_model"]["outcome"], "mismatch")

    def test_wrong_properties_sha256_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta",
                                  provenance_overrides={"sha256_control_properties": "1" * 64})
        entry = self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")
        checks = {c["check"]: c for c in entry["provenance"]["checks"]}
        self.assertEqual(checks["sha256_control_properties"]["outcome"], "mismatch")

    def test_wrong_depth_in_provenance_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta", provenance_overrides={"depth": "4"})
        self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")

    def test_wrong_strategy_in_provenance_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta", provenance_overrides={"strategy": "dfs"})
        self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")

    def test_wrong_config_identity_in_provenance_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta",
                                  provenance_overrides={"config_id": "B9_K8_T1_atlanta"})
        self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")

    def test_wrong_benchmark_identity_in_provenance_is_provenance_mismatch(self):
        self.fixture.write_config("B1_K8_T1_atlanta",
                                  provenance_overrides={"benchmark": "benchmarks/final/b1_waypoint_order_churn/K8/T9_bogus"})
        self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")

    def test_cross_contaminated_provenance_paths_are_detected(self):
        self.fixture.write_config("B1_K8_T1_atlanta",
                                  provenance_overrides={"bad_model_path": "/repo/benchmarks/final/b1_waypoint_order_churn/K8/T1_atlanta/control/model.json"})
        self.assert_classification("B1_K8_T1_atlanta", "PROVENANCE_MISMATCH")

    def test_missing_benchmark_input_is_provenance_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        self.fixture.write_config(config_id)
        bench = self.fixture.repo / self.fixture.exp(config_id)["benchmark_dir"]
        (bench / "bad" / "model.json").unlink()
        entry = self.assert_classification(config_id, "PROVENANCE_MISMATCH")
        checks = {c["check"]: c for c in entry["provenance"]["checks"]}
        self.assertEqual(checks["sha256_bad_model"]["outcome"], "unverifiable")

    def test_bad_control_evidence_swap_is_detected(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None},
                                               "control": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        bad_cache = fixture.cache(config_id, "bad")
        control_cache = fixture.cache(config_id, "control")
        bad_console = console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"], bad_cache)
        control_console = console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["control_harmful"], control_cache)
        bad_csv = final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"], bad_cache)
        control_csv = final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["control_harmful"], control_cache)
        (cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log").write_text(control_console, encoding="utf-8")
        (cfg_dir / "console" / f"{exp['log_base']}_control_depth{exp['depth']}.log").write_text(bad_console, encoding="utf-8")
        (cfg_dir / "artifacts" / "bad" / "final_stats.csv").write_text(control_csv, encoding="utf-8")
        (cfg_dir / "artifacts" / "control" / "final_stats.csv").write_text(bad_csv, encoding="utf-8")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)
        entry = fixture.config_report(report, config_id)
        self.assertNotEqual(entry["classification"], "SCIENTIFIC_MATCH")

    def test_zero_harmful_control_with_empty_trace_dirs_is_valid(self):
        config_id = "B1_K8_T1_atlanta"
        self.fixture.write_config(config_id, sides={"control": {"harmful_trace_files": 0}})
        code, report = self.fixture.run_report()
        entry = self.fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        hte = entry["sides"]["control"]["harmful_trace_evidence"]
        self.assertEqual(hte["outcome"], "not_required")

    def test_nonzero_harmful_with_preserved_traces_is_valid(self):
        config_id = "B1_K8_T1_atlanta"
        self.fixture.write_config(config_id, sides={"bad": {"harmful_trace_files": 3}})
        code, report = self.fixture.run_report()
        entry = self.fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        hte = entry["sides"]["bad"]["harmful_trace_evidence"]
        self.assertEqual(hte["outcome"], "present")
        self.assertEqual(hte["harmful_trace_files"], 3)

    def test_nonzero_harmful_without_traces_is_incomplete(self):
        config_id = "B1_K8_T1_atlanta"
        self.fixture.write_config(config_id, sides={"bad": {"run_dirs": False}})
        entry = self.assert_classification(config_id, "INCOMPLETE_EVIDENCE")
        hte = entry["sides"]["bad"]["harmful_trace_evidence"]
        self.assertEqual(hte["outcome"], "missing")

    def test_missing_historical_cache_is_reported_unavailable(self):
        config_id = "B1_K8_T1_atlanta"
        self.fixture.write_config(config_id)
        log_dir = self.fixture.repo / "docs" / "validation_logs" / "main"
        (log_dir / f"{config_id}_control.txt").unlink()
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        entry = self.fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "SCIENTIFIC_MATCH", msg=json.dumps(entry["issues"], indent=2))
        self.assertIsNone(entry["expected"]["historical_cache"]["control"])
        comparisons = entry["sides"]["control"]["comparisons"]
        self.assertTrue(any(c["outcome"] == "unavailable" and c["source"] == "historical_log" for c in comparisons))

    def test_historical_cache_mismatch_is_scientific_mismatch(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        cache = dict(fixture.cache(config_id, "bad"))
        cache["katch_cache_hits"] += 1
        fixture.write_config(config_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(config_id)
        cfg_dir = fixture.matrix / config_id
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        console_path.write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        csv_path = cfg_dir / "artifacts" / "bad" / "final_stats.csv"
        csv_path.write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"], cache),
            encoding="utf-8")
        entry = self.assert_classification(config_id, "SCIENTIFIC_MISMATCH")
        katch = [c for c in entry["sides"]["bad"]["comparisons"] if c["field"] == "katch_cache_hits"]
        self.assertEqual(katch[0]["outcome"], "mismatch")
        self.assertEqual(katch[0]["source"], "historical_log")

    def test_all_16_configurations_are_reported(self):
        for config_id in self.fixture.order[:3]:
            self.fixture.write_config(config_id)
        self.fixture.write_config(self.fixture.order[3], status="FAILED", exit_code="1", detail="pair runner failed")
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        self.assertEqual(len(report["configurations"]), 16)
        classifications = {c["config_id"]: c["classification"] for c in report["configurations"]}
        self.assertEqual(classifications[self.fixture.order[0]], "SCIENTIFIC_MATCH")
        self.assertEqual(classifications[self.fixture.order[3]], "INFRASTRUCTURE_FAILURE")
        self.assertEqual(classifications[self.fixture.order[4]], "NOT_RUN")
        self.assertEqual(report["overall"]["total_configurations"], 16)

    def test_mixed_matrix_returns_nonzero(self):
        fixture = self.fixture
        fixture.write_config(fixture.order[0])
        mismatch_id = fixture.order[1]
        fixture.write_config(mismatch_id, sides={"bad": {"console": None, "csv": None}})
        exp = fixture.exp(mismatch_id)
        cfg_dir = fixture.matrix / mismatch_id
        cache = fixture.cache(mismatch_id, "bad")
        (cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log").write_text(
            console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], 999, cache),
            encoding="utf-8")
        (cfg_dir / "artifacts" / "bad" / "final_stats.csv").write_text(
            final_stats_csv_text(exp["depth"], "bfs", exp["branches"], exp["traces"], 999, cache),
            encoding="utf-8")
        fixture.write_config(fixture.order[2], status="FAILED", exit_code="3", detail="pair runner failed")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)
        self.assertFalse(report["overall"]["success"])
        counts = report["overall"]["classification_counts"]
        self.assertEqual(counts.get("SCIENTIFIC_MATCH"), 1)
        self.assertEqual(counts.get("SCIENTIFIC_MISMATCH"), 1)
        self.assertEqual(counts.get("INFRASTRUCTURE_FAILURE"), 1)
        self.assertEqual(counts.get("NOT_RUN"), 13)

    def test_partial_matrix_does_not_pass(self):
        self.fixture.write_config(self.fixture.order[0])
        code, report = self.fixture.run_report()
        self.assertEqual(code, 1)
        self.assertFalse(report["overall"]["success"])
        self.assertEqual(report["overall"]["classification_counts"].get("NOT_RUN"), 15)

    def test_malformed_files_are_handled_safely(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id)
        cfg_dir = fixture.matrix / config_id
        (cfg_dir / "provenance.tsv").write_text("this line has no equals sign\nalso bad\n", encoding="utf-8")
        exp = fixture.exp(config_id)
        console_path = cfg_dir / "console" / f"{exp['log_base']}_bad_depth{exp['depth']}.log"
        text = console_log_text(exp["depth"], "bfs", exp["branches"], exp["traces"], exp["bad_harmful"],
                                fixture.cache(config_id, "bad"))
        truncated = text[:text.index("=================================")]
        console_path.write_text(truncated, encoding="utf-8")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "INCOMPLETE_EVIDENCE")
        self.assertTrue(any("provenance" in issue["detail"].lower() for issue in entry["issues"]))

    def test_malformed_status_rows_are_handled_safely(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id)
        fixture.status_override = ("\t".join(checker.STATUS_HEADER) + "\n"
                                   "B1_K8_T1_atlanta\tonly-three-fields\n")
        code, report = fixture.run_report()
        self.assertEqual(code, 1)
        entry = fixture.config_report(report, config_id)
        self.assertEqual(entry["classification"], "INCOMPLETE_EVIDENCE")
        self.assertTrue(report["status_file"]["warnings"])

    def test_wrong_status_header_is_environment_error(self):
        fixture = self.fixture
        fixture.write_config("B1_K8_T1_atlanta")
        fixture.status_override = "a\tb\tc\n"
        code, out = fixture.run_check()
        self.assertEqual(code, 2)

    def test_json_output_is_parseable_and_stable(self):
        self.write_all_valid()
        code1, out1 = self.fixture.run_check(json_mode=True)
        code2, out2 = self.fixture.run_check(json_mode=True)
        self.assertEqual(code1, code2)
        report1 = json.loads(out1)
        report2 = json.loads(out2)
        self.assertEqual(report1["schema"], "raceloom-matrix-check-report-v1")
        report1.pop("generated_utc")
        report2.pop("generated_utc")
        self.assertEqual(report1, report2)
        self.assertIn("overall", report1)
        self.assertIn("configurations", report1)
        self.assertIn("timing_policy", report1)

    def test_output_file_refuses_overwrite(self):
        self.write_all_valid()
        target = Path(self._tmp) / "report.json"
        target.write_text("existing content\n", encoding="utf-8")
        code, _ = self.fixture.run_check(extra_args=["--output", str(target)])
        self.assertEqual(code, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "existing content\n")

    def test_output_file_writes_new_json_report(self):
        self.write_all_valid()
        target = Path(self._tmp) / "subdir-report.json"
        code, _ = self.fixture.run_check(extra_args=["--output", str(target)])
        self.assertEqual(code, 0)
        report = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "raceloom-matrix-check-report-v1")
        self.assertTrue(report["overall"]["success"])

    def test_checker_does_not_modify_any_files(self):
        self.write_all_valid()
        self.fixture.write_status()
        before = self.fixture.tree_snapshot()
        self.fixture.run_check()
        self.fixture.run_check(json_mode=True)
        after = self.fixture.tree_snapshot()
        self.assertEqual(before, after)

    def test_execution_scripts_remain_untouched(self):
        config_id = "B1_K8_T1_atlanta"
        fixture = self.fixture
        fixture.write_config(config_id)
        scripts_dir = fixture.repo / "scripts"
        scripts_dir.mkdir()
        script_paths = {}
        for name in ("run_one_pair.sh", "run_raceloom_progress.sh", "run_final_matrix.sh"):
            path = scripts_dir / name
            path.write_text(f"#!/bin/sh\n# synthetic {name}\n", encoding="utf-8")
            script_paths[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        fixture.run_check()
        for name, digest in script_paths.items():
            self.assertEqual(hashlib.sha256((scripts_dir / name).read_bytes()).hexdigest(), digest)

    def test_status_record_without_directory_is_incomplete(self):
        fixture = self.fixture
        exp = fixture.exp("B1_K8_T1_atlanta")
        fixture.status_records.append({
            "config_id": "B1_K8_T1_atlanta",
            "benchmark": exp["benchmark_dir"],
            "depth": "5",
            "status": "COMPLETE",
            "exit_code": "0",
            "utc_start": "2026-11-03T10:00:00Z",
            "utc_end": "2026-11-03T10:30:00Z",
            "evidence_dir": "/nowhere/B1_K8_T1_atlanta",
            "detail": "orphaned record",
        })
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_complete_marker_without_status_record_is_incomplete(self):
        self.fixture.write_config("B1_K8_T1_atlanta", status=None)
        self.assert_classification("B1_K8_T1_atlanta", "INCOMPLETE_EVIDENCE")

    def test_skipped_already_complete_is_operational_success(self):
        self.fixture.write_config("B1_K8_T1_atlanta", status="SKIPPED_ALREADY_COMPLETE",
                                  detail="valid completion evidence found; skipped without executing")
        entry = self.assert_classification("B1_K8_T1_atlanta", "SCIENTIFIC_MATCH")
        self.assertEqual(entry["operational"]["last_status"], "SKIPPED_ALREADY_COMPLETE")

    def test_failed_then_blocked_records_report_infrastructure_failure(self):
        fixture = self.fixture
        blocked_detail = "existing incomplete, failed, or unrecognized evidence; not rerun automatically; manual recovery required"
        fixture.write_config("B1_K8_T1_atlanta", status="BLOCKED", exit_code="-", detail=blocked_detail,
                             extra_records=[], provenance=False, complete_marker=False)
        first = fixture.status_records[-1]
        fixture.status_records[-1] = dict(first, status="FAILED", exit_code="2", detail="pair runner failed")
        fixture.status_records.append(dict(first))
        self.assert_classification("B1_K8_T1_atlanta", "INFRASTRUCTURE_FAILURE")

    def test_environment_error_for_missing_matrix_root(self):
        code, _ = self.fixture.run_check(extra_args=["--matrix-root", "/nonexistent/matrix-root"])
        self.assertEqual(code, 2)

    def test_environment_error_for_missing_matrix_tsv(self):
        fixture = self.fixture
        (fixture.repo / "docs" / "final_4x4_matrix.tsv").unlink()
        fixture.write_config("B1_K8_T1_atlanta")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_environment_error_for_truncated_matrix_tsv(self):
        fixture = self.fixture
        tsv = fixture.repo / "docs" / "final_4x4_matrix.tsv"
        lines = tsv.read_text(encoding="utf-8").splitlines()
        tsv.write_text("\n".join(lines[:10]) + "\n", encoding="utf-8")
        fixture.write_config("B1_K8_T1_atlanta")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_environment_error_for_malformed_tsv_row(self):
        fixture = self.fixture
        tsv = fixture.repo / "docs" / "final_4x4_matrix.tsv"
        lines = tsv.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1].replace("\t156100\t", "\tnot-a-number\t")
        tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fixture.write_config("B1_K8_T1_atlanta")
        code, _ = fixture.run_check()
        self.assertEqual(code, 2)

    def test_checker_uses_no_subprocess_or_network_modules(self):
        source = Path(checker.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "urllib", "requests", "http.client", "docker"):
            self.assertNotIn(f"import {forbidden}", source)
            self.assertNotIn(f"from {forbidden}", source)

    def test_human_output_contains_summary_and_findings(self):
        fixture = self.fixture
        fixture.write_config(fixture.order[0])
        fixture.write_config(fixture.order[1], sides={"bad": {"csv_overrides": {"harmfulRaces": "999"}}})
        code, out = fixture.run_check()
        self.assertEqual(code, 1)
        self.assertIn("per-configuration results:", out)
        self.assertIn("SCIENTIFIC_MISMATCH", out)
        self.assertIn("findings:", out)
        self.assertIn("OVERALL: FAIL", out)
        self.assertIn("sides with valid evidence:", out)

    def test_human_output_pass_line_for_full_matrix(self):
        self.write_all_valid()
        code, out = self.fixture.run_check()
        self.assertEqual(code, 0)
        self.assertIn("OVERALL: PASS - all 16 configurations scientifically matched", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
