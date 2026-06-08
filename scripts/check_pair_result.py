#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

def last(pattern, text):
    matches = re.findall(pattern, text)
    return matches[-1] if matches else None

def read_stats(path):
    text = Path(path).read_text(errors="ignore")
    return {
        "traces": last(r"Generated traces:\s*([0-9]+)", text),
        "harmful": last(r"Harmful races found:\s*([0-9]+)", text),
        "total": last(r"Total execution time:\s*([0-9.]+)", text),
        "finished": "RaceLoom finished with exit code: 0" in text or "Final Stats" in text,
    }

ap = argparse.ArgumentParser()
ap.add_argument("--bad-log", required=True)
ap.add_argument("--control-log", required=True)
ap.add_argument("--expected-traces", type=int)
ap.add_argument("--expected-bad-harmful", type=int)
ap.add_argument("--expected-control-harmful", type=int, default=0)
args = ap.parse_args()

bad = read_stats(args.bad_log)
control = read_stats(args.control_log)

errors = []

for name, stats in [("bad", bad), ("control", control)]:
    if not stats["finished"]:
        errors.append(f"{name}: log does not look complete")
    if stats["traces"] is None:
        errors.append(f"{name}: missing Generated traces")
    if stats["harmful"] is None:
        errors.append(f"{name}: missing Harmful races found")

if not errors:
    bad_traces = int(bad["traces"])
    control_traces = int(control["traces"])
    bad_harmful = int(bad["harmful"])
    control_harmful = int(control["harmful"])

    if args.expected_traces is not None:
        if bad_traces != args.expected_traces:
            errors.append(f"bad: expected {args.expected_traces} traces, got {bad_traces}")
        if control_traces != args.expected_traces:
            errors.append(f"control: expected {args.expected_traces} traces, got {control_traces}")

    if args.expected_bad_harmful is not None and bad_harmful != args.expected_bad_harmful:
        errors.append(f"bad: expected {args.expected_bad_harmful} harmful races, got {bad_harmful}")

    if control_harmful != args.expected_control_harmful:
        errors.append(f"control: expected {args.expected_control_harmful} harmful races, got {control_harmful}")

    if bad_harmful <= 0:
        errors.append("bad: expected at least one harmful race")
    if control_harmful != 0:
        errors.append("control: expected zero harmful races")

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("PASS")
print(f"bad:     traces={bad['traces']} harmful={bad['harmful']} total={bad['total']}s")
print(f"control: traces={control['traces']} harmful={control['harmful']} total={control['total']}s")
