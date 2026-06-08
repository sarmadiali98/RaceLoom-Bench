#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def last(pattern: str, text: str) -> str:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    return matches[-1].strip() if matches else ""


def safe_case(s: str) -> str:
    s = s.replace("/", "_")
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    return s.strip("_")


def expected_log_path(log_root: Path, row: dict[str, str]) -> Path:
    if row["set"] == "main":
        return log_root / "main" / f"{row['id']}_{safe_case(row['topology_or_case'])}_{row['side']}.txt"
    if row["set"] == "synthetic":
        return log_root / "synthetic" / f"{row['id']}_{row['side']}.txt"
    raise SystemExit(f"Unknown benchmark set: {row['set']}")


def parse_raceloom_log(path: Path) -> dict[str, str]:
    text = path.read_text(errors="ignore")
    return {
        "branches": last(r"Network model branches:\s*(.+)", text),
        "traces": last(r"Generated traces:\s*([0-9]+)", text),
        "harmful": last(r"Harmful races found:\s*([0-9]+)", text),
        "total_seconds": last(r"Total execution time:\s*([0-9.]+)", text),
    }


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def validate_against_manifest(row: dict[str, str], parsed: dict[str, str], log_path: Path) -> None:
    checks = ["branches", "traces", "harmful", "total_seconds"]
    for key in checks:
        if not parsed.get(key):
            raise SystemExit(f"Missing {key} in {log_path}")
        if str(parsed[key]) != str(row[key]):
            raise SystemExit(
                f"Mismatch for {key} in {log_path}\n"
                f"  manifest: {row[key]}\n"
                f"  log:      {parsed[key]}"
            )


def write_main_matrix(rows: list[dict[str, str]], path: Path) -> None:
    main = [r for r in rows if r["set"] == "main"]

    grouped: dict[tuple[str, str, str, str], dict[str, dict[str, str]]] = {}
    for r in main:
        key = (r["id"], r["family_or_scenario"], r["benchmark_dir"], r["topology_or_case"])
        grouped.setdefault(key, {})[r["side"]] = r

    lines = [
        "# Reproduced B1--B4 matrix from validation logs",
        "",
        "Each entry is `traces / faulty harmful races / control harmful races`.",
        "",
        "| ID | Family | Case | Result |",
        "|---|---|---|---:|",
    ]

    for key in sorted(grouped):
        bid, family, _bench_dir, case = key
        pair = grouped[key]
        bad = pair.get("bad")
        control = pair.get("control")
        if bad is None or control is None:
            raise SystemExit(f"Missing bad/control pair for {key}")
        if bad["traces"] != control["traces"]:
            raise SystemExit(f"Trace mismatch for {key}: {bad['traces']} vs {control['traces']}")

        lines.append(
            f"| {bid} | {family} | {case} | "
            f"{int(bad['traces']):,} / {bad['harmful']} / {control['harmful']} |"
        )

    path.write_text("\n".join(lines) + "\n")


def write_synthetic_matrix(rows: list[dict[str, str]], path: Path) -> None:
    synthetic = [r for r in rows if r["set"] == "synthetic"]

    grouped: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    for r in synthetic:
        key = (r["id"], r["family_or_scenario"])
        grouped.setdefault(key, {})[r["side"]] = r

    lines = [
        "# Reproduced S1--S4 matrix from validation logs",
        "",
        "Each entry is `traces / faulty harmful races / control harmful races`.",
        "",
        "| ID | Scenario | Result |",
        "|---|---|---:|",
    ]

    for key in sorted(grouped):
        sid, scenario = key
        pair = grouped[key]
        bad = pair.get("bad")
        control = pair.get("control")
        if bad is None or control is None:
            raise SystemExit(f"Missing bad/control pair for {key}")
        if bad["traces"] != control["traces"]:
            raise SystemExit(f"Trace mismatch for {key}: {bad['traces']} vs {control['traces']}")

        lines.append(
            f"| {sid} | {scenario} | "
            f"{int(bad['traces']):,} / {bad['harmful']} / {control['harmful']} |"
        )

    path.write_text("\n".join(lines) + "\n")


def check_committed_summaries(rows: list[dict[str, str]]) -> None:
    final_tsv = Path("docs/final_4x4_matrix.tsv")
    synthetic_tsv = Path("docs/synthetic_s1_s4_matrix.tsv")

    if final_tsv.exists():
        final_rows = read_tsv(final_tsv)

        main_pairs: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
        for r in rows:
            if r["set"] != "main":
                continue
            topology = r["topology_or_case"].split("/", 1)[1]
            key = (r["id"], topology)
            main_pairs.setdefault(key, {})[r["side"]] = r

        for fr in final_rows:
            # Committed benchmark names are descriptive strings such as
            # B1_waypoint_order, while the validation manifest stores the
            # canonical ID separately as B1/B2/B3/B4.
            bid = fr["benchmark"].split("_", 1)[0]
            key = (bid, fr["topology"])
            pair = main_pairs.get(key)
            if not pair or "bad" not in pair or "control" not in pair:
                raise SystemExit(f"Missing reproduced main pair for committed row {key}")

            bad = pair["bad"]
            control = pair["control"]
            expected = {
                "traces": fr["traces"],
                "bad_harmful": fr["bad_harmful"],
                "control_harmful": fr["control_harmful"],
            }
            actual = {
                "traces": bad["traces"],
                "bad_harmful": bad["harmful"],
                "control_harmful": control["harmful"],
            }
            if expected != actual:
                raise SystemExit(f"Main summary mismatch for {key}: expected {expected}, actual {actual}")

    if synthetic_tsv.exists():
        syn_rows = read_tsv(synthetic_tsv)

        syn_pairs: dict[str, dict[str, dict[str, str]]] = {}
        for r in rows:
            if r["set"] != "synthetic":
                continue
            syn_pairs.setdefault(r["id"], {})[r["side"]] = r

        for sr in syn_rows:
            sid = sr["ID"]
            pair = syn_pairs.get(sid)
            if not pair or "bad" not in pair or "control" not in pair:
                raise SystemExit(f"Missing reproduced synthetic pair for {sid}")

            bad = pair["bad"]
            control = pair["control"]
            expected = {
                "traces": sr["Generated traces"],
                "bad_harmful": sr["Bad harmful races"],
                "control_harmful": sr["Control harmful races"],
            }
            actual = {
                "traces": bad["traces"],
                "bad_harmful": bad["harmful"],
                "control_harmful": control["harmful"],
            }
            if expected != actual:
                raise SystemExit(f"Synthetic summary mismatch for {sid}: expected {expected}, actual {actual}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="docs/validation_logs")
    ap.add_argument("--manifest", default="docs/benchmark_runtimes_exact.tsv")
    ap.add_argument("--out", default="reproduced_paper_numbers")
    args = ap.parse_args()

    log_root = Path(args.logs)
    manifest = Path(args.manifest)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    manifest_rows = read_tsv(manifest)
    if len(manifest_rows) != 40:
        raise SystemExit(f"Expected 40 manifest rows, found {len(manifest_rows)}")

    reproduced: list[dict[str, str]] = []

    for row in manifest_rows:
        log_path = expected_log_path(log_root, row)
        if not log_path.exists():
            raise SystemExit(f"Missing validation log: {log_path}")

        parsed = parse_raceloom_log(log_path)
        validate_against_manifest(row, parsed, log_path)

        reproduced.append({
            "set": row["set"],
            "id": row["id"],
            "family_or_scenario": row["family_or_scenario"],
            "benchmark_dir": row["benchmark_dir"],
            "topology_or_case": row["topology_or_case"],
            "side": row["side"],
            "depth": row["depth"],
            "branches": parsed["branches"],
            "traces": parsed["traces"],
            "harmful": parsed["harmful"],
            "total_seconds": parsed["total_seconds"],
            "log_file": str(log_path),
        })

    check_committed_summaries(reproduced)

    fields = [
        "set",
        "id",
        "family_or_scenario",
        "benchmark_dir",
        "topology_or_case",
        "side",
        "depth",
        "branches",
        "traces",
        "harmful",
        "total_seconds",
        "log_file",
    ]

    write_tsv(out / "reproduced_from_logs.tsv", reproduced, fields)
    write_main_matrix(reproduced, out / "reproduced_final_4x4_matrix.md")
    write_synthetic_matrix(reproduced, out / "reproduced_synthetic_s1_s4_matrix.md")

    print(f"Parsed and verified {len(reproduced)} validation logs.")
    print("Checked reproduced numbers against committed summary TSV files.")
    print(f"Wrote {out / 'reproduced_from_logs.tsv'}")
    print(f"Wrote {out / 'reproduced_final_4x4_matrix.md'}")
    print(f"Wrote {out / 'reproduced_synthetic_s1_s4_matrix.md'}")


if __name__ == "__main__":
    main()
