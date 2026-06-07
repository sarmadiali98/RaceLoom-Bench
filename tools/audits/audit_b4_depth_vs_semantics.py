#!/usr/bin/env python3
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("benchmarks_comprehensive_topologies")

T1 = ROOT / "b4_failover_cleanup_churn/K8/T1_atlanta"
T2 = ROOT / "b4_failover_cleanup_churn/K12/T2_nobel_eu"

CORE = ["CDetect", "CFailover", "CCleanup"]

def read_json(p):
    return json.loads(Path(p).read_text())

def parse_log(p):
    p = Path(p)
    if not p.exists():
        return None

    txt = p.read_text(errors="ignore")
    blocks = txt.split("========== Final Stats ==========")
    if len(blocks) < 2:
        return {"status": "NO_FINAL_STATS", "path": str(p), "tail": "\n".join(txt.splitlines()[-20:])}

    block = blocks[-1]

    def get(label):
        m = re.search(rf"{re.escape(label)}:\s*([^\n]+)", block)
        return m.group(1).strip() if m else None

    return {
        "status": "DONE",
        "path": str(p),
        "branches": get("Network model branches"),
        "traces": get("Generated traces"),
        "harmful": get("Harmful races found"),
        "total": get("Total execution time"),
    }

def props_summary(side_dir):
    p = read_json(side_dir / "properties.json")
    return {
        k: v.get("Expression")
        for k, v in p.get("Properties", {}).items()
    }

def non_bg_updates(model):
    out = []
    for sw, data in sorted(model["Switches"].items()):
        for u in data.get("DirectUpdates", []):
            ch = str(u.get("Channel", ""))
            if not ch.startswith("upBg"):
                out.append((sw, ch, u.get("Policy")))
    return out

def non_bg_update_multiset(model):
    return Counter((ch, pol) for _, ch, pol in non_bg_updates(model))

def nonzero_tables(model):
    out = []
    for sw, data in sorted(model["Switches"].items()):
        init = data.get("InitialFlowTable", "zero")
        if init != "zero":
            out.append((sw, init))
    return out

def atomic_terms(s):
    # Normalize either a single table or a union of tables into atomic forwarding terms.
    # Example:
    #   (((port = 9205) . (port <- 9206)) + ((port = 9202) . (port <- 9203)))
    # becomes two atoms.
    atoms = re.findall(r"\(port\s*=\s*\d+\)\s*\.\s*\(port\s*<-\s*\d+\)", str(s))
    return [re.sub(r"\s+", " ", a).strip() for a in atoms]

def nonzero_table_multiset(model):
    c = Counter()
    for _, init in nonzero_tables(model):
        for atom in atomic_terms(init):
            c[atom] += 1
    return c

def rec_core(model):
    return {k: model.get("RecursiveVariables", {}).get(k) for k in CORE}

def compare_side(side):
    print()
    print("=" * 100)
    print(f"STATIC SEMANTIC CHECK: {side.upper()}")
    print("=" * 100)

    t1m = read_json(T1 / side / "model.json")
    t2m = read_json(T2 / side / "model.json")

    print()
    print("controllers")
    print("  T1:", t1m.get("Controllers"))
    print("  T2:", t2m.get("Controllers"))

    print()
    print("recursive core vars exact match?")
    for c in CORE:
        same = rec_core(t1m)[c] == rec_core(t2m)[c]
        print(f"  {c}: {same}")
        if not same:
            print("    T1:", rec_core(t1m)[c])
            print("    T2:", rec_core(t2m)[c])

    print()
    print("non-bg update channel/policy multiset exact match?")
    u1 = non_bg_update_multiset(t1m)
    u2 = non_bg_update_multiset(t2m)
    print("  match:", u1 == u2)
    if u1 != u2:
        print("  only in T1:", u1 - u2)
        print("  only in T2:", u2 - u1)

    print()
    print("nonzero initial-table multiset exact match?")
    it1 = nonzero_table_multiset(t1m)
    it2 = nonzero_table_multiset(t2m)
    print("  match:", it1 == it2)
    if it1 != it2:
        print("  only in T1:", it1 - it2)
        print("  only in T2:", it2 - it1)

    print()
    print("T2 placement of nonzero tables:")
    for sw, init in nonzero_tables(t2m):
        print(" ", sw, "=", init)

    print()
    print("T2 placement of core direct updates:")
    for sw, ch, pol in non_bg_updates(t2m):
        print(" ", sw, ch, "=", pol)

    print()
    print("properties exact match?")
    p1 = props_summary(T1 / side)
    p2 = props_summary(T2 / side)
    print("  match:", p1 == p2)
    print("  T1:", p1)
    print("  T2:", p2)

def compare_bad_control(base, label):
    print()
    print("=" * 100)
    print(f"BAD VS CONTROL DIFF: {label}")
    print("=" * 100)

    bad = read_json(base / "bad/model.json")
    ctrl = read_json(base / "control/model.json")

    b_up = non_bg_update_multiset(bad)
    c_up = non_bg_update_multiset(ctrl)

    print()
    print("non-bg direct update difference:")
    print("  bad-only:", b_up - c_up)
    print("  control-only:", c_up - b_up)

    b_rec = rec_core(bad)
    c_rec = rec_core(ctrl)

    print()
    print("recursive core var differences:")
    for k in CORE:
        if b_rec[k] != c_rec[k]:
            print(" ", k)
            print("    bad:    ", b_rec[k])
            print("    control:", c_rec[k])

def print_logs():
    print()
    print("=" * 100)
    print("LOG CHECK")
    print("=" * 100)

    candidates = [
        ("T1 bad depth 5 locked", T1 / "bad_depth5_bfs.log"),
        ("T1 control depth 5 locked", T1 / "control_depth5_bfs.log"),
        ("T2 bad depth 4 failed", T2 / "bad_depth4_bfs.log"),
        ("T2 control depth 4", T2 / "control_depth4_bfs.log"),
        ("T2 bad depth 5 candidate", T2 / "bad_depth5_bfs.nohup.log"),
    ]

    for label, path in candidates:
        print()
        print(label)
        res = parse_log(path)
        if res is None:
            print("  MISSING:", path)
            continue

        print("  status:", res["status"])
        print("  path:", res["path"])

        if res["status"] == "DONE":
            print("  branches:", res["branches"])
            print("  traces:", res["traces"])
            print("  harmful:", res["harmful"])
            print("  total:", res["total"])
        else:
            print("  no final stats yet")
            print("  last log lines:")
            print(res["tail"])

def conclusion():
    print()
    print("=" * 100)
    print("HOW TO READ THIS")
    print("=" * 100)

    print("""
If the static checks say:
  recursive core vars exact match = True
  non-bg update channel/policy multiset exact match = True
  nonzero initial-table multiset exact match = True
  properties exact match = True

then the T2 model probably preserved the T1 B4 symbolic semantics, and the depth-4 failure is more likely a depth/interleaving issue.

If any of those are False, especially recursive vars / core updates / initial tables / properties, then the problem is not just depth: the B4 generator changed the benchmark semantics or mapping.

Runtime evidence:
  T2 depth 4 bad = 0 harmful
  T2 depth 5 bad > 0 harmful  => depth was the issue
  T2 depth 5 bad = 0 harmful  => likely semantics/mapping issue, or B4 needs a different construction for T2
""")

for side in ["bad", "control"]:
    compare_side(side)

compare_bad_control(T1, "T1 locked reference")
compare_bad_control(T2, "T2 generated candidate")

print_logs()
conclusion()
