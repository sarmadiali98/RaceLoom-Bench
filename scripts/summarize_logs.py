#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def parse_log(path):
    txt = Path(path).read_text(errors="ignore")
    blocks = txt.split("========== Final Stats ==========")
    if len(blocks) < 2:
        return None
    block = blocks[-1]

    def get(label):
        m = re.search(rf"{re.escape(label)}:\s*([^\n]+)", block)
        return m.group(1).strip() if m else ""

    return {
        "log": str(path),
        "branches": get("Network model branches"),
        "traces": get("Generated traces"),
        "harmful": get("Harmful races found"),
        "total_seconds": get("Total execution time"),
    }

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results")
logs = sorted(root.rglob("*.log"))

print("log\tbranches\ttraces\tharmful\ttotal_seconds")
for log in logs:
    row = parse_log(log)
    if row:
        print(f'{row["log"]}\t{row["branches"]}\t{row["traces"]}\t{row["harmful"]}\t{row["total_seconds"]}')
