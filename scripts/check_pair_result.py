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
        "branches": last(r"Network model branches:\s*([A-Za-z0-9_;:]+)", text),
        "total": last(r"Total execution time:\s*([0-9.]+)", text),
        "finished": "RaceLoom finished with exit code: 0" in text or "Final Stats" in text,
    }

def parse_branches(signature):
    """Parse 'CRoute:1;BSw:2' into {name: count}; None on malformed input."""
    if signature is None:
        return None
    mapping = {}
    for part in signature.split(";"):
        if ":" not in part:
            return None
        name, _, count = part.rpartition(":")
        if not name or not count.isdigit():
            return None
        if name in mapping:
            return None
        mapping[name] = int(count)
    return mapping

ap = argparse.ArgumentParser()
ap.add_argument("--bad-log", required=True)
ap.add_argument("--control-log", required=True)
ap.add_argument("--expected-traces", type=int)
ap.add_argument("--expected-bad-harmful", type=int)
ap.add_argument("--expected-control-harmful", type=int, default=0)
ap.add_argument("--expected-branches", default=None,
                help="expected branch signature, e.g. 'CRoute:1;BSw:2'; "
                     "compared order-independently against both logs")
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

expected_branches = parse_branches(args.expected_branches)
if args.expected_branches is not None and expected_branches is None:
    errors.append(f"malformed --expected-branches value: {args.expected_branches!r}")

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

    if expected_branches is not None:
        for name, stats in [("bad", bad), ("control", control)]:
            actual = parse_branches(stats["branches"])
            if actual is None:
                errors.append(f"{name}: missing or malformed branch signature")
            elif actual != expected_branches:
                errors.append(
                    f"{name}: branch signature mismatch: expected {args.expected_branches}, "
                    f"got {stats['branches']}"
                )

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("PASS")
print(f"bad:     traces={bad['traces']} harmful={bad['harmful']} branches={bad['branches']} total={bad['total']}s")
print(f"control: traces={control['traces']} harmful={control['harmful']} branches={control['branches']} total={control['total']}s")
