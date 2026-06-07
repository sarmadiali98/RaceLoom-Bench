#!/usr/bin/env python3
import json
import shutil
from pathlib import Path

ROOT = Path("benchmarks_comprehensive_topologies")
ASSETS = ROOT / "_topology_assets"

ARCHIVES = sorted(ROOT.glob("_deprecated_L_named_*"))
if not ARCHIVES:
    raise SystemExit("No _deprecated_L_named_* archive found.")
ARCHIVE = ARCHIVES[-1]

T1_B4 = ROOT / "b4_failover_cleanup_churn" / "K8" / "T1_atlanta"

JOBS_TEMPLATE = [
    ("K12", "T2_nobel_eu", 4),
    ("K16", "T4_germany50", 4),
]

GEANT_JOB = ("K14", "T3_geant2012", 4, 14)

CORE_CONTROLLERS = ["CDetect", "CFailover", "CCleanup"]

def read_json(p):
    return json.loads(Path(p).read_text())

def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n")

def sw_name(node):
    return "SW" + "".join(c for c in str(node) if c.isdigit())

def term(i, o):
    return f"(port = {i}) . (port <- {o})"

def link(i, o):
    return f"((port = {i}) . (port <- {o}))"

def union(parts):
    cleaned = []
    for p in parts:
        if not p:
            continue
        p = str(p).strip()
        if not p or p == "zero":
            continue
        cleaned.append(p)
    cleaned = list(dict.fromkeys(cleaned))
    if not cleaned:
        return "zero"
    if len(cleaned) == 1:
        return cleaned[0]
    return "(" + " + ".join(f"({p})" for p in cleaned) + ")"

def add_links(existing, extra):
    return union([existing, extra])

def merge_table(existing, new):
    return union([existing, new])

def load_asset(topo):
    p = ASSETS / f"{topo}.json"
    if not p.exists():
        raise SystemExit(f"Missing topology asset: {p}")
    return read_json(p)

def role_switches_from_asset(topo):
    asset = load_asset(topo)
    anchors = asset["default_anchors"]
    path = anchors.get("diameter_path", [])

    source_sw = sw_name(anchors["source"])
    endpoint_sw = sw_name(anchors["destination"])
    preferred_core = sw_name(anchors["waypoint_on_diameter_path"])

    used = {source_sw, endpoint_sw}
    core_sws = []

    if preferred_core not in used:
        core_sws.append(preferred_core)
        used.add(preferred_core)

    for n in path:
        sw = sw_name(n)
        if sw not in used:
            core_sws.append(sw)
            used.add(sw)

    for n in asset["nodes"]:
        sw = sw_name(n)
        if sw not in used:
            core_sws.append(sw)
            used.add(sw)

    return {
        "asset": asset,
        "source_sw": source_sw,
        "endpoint_sw": endpoint_sw,
        "core_sws": core_sws,
    }

def non_bg_updates(data):
    return [
        u for u in data.get("DirectUpdates", [])
        if not str(u.get("Channel", "")).startswith("upBg")
    ]

def bg_updates(data):
    return [
        u for u in data.get("DirectUpdates", [])
        if str(u.get("Channel", "")).startswith("upBg")
    ]

def extract_t1_gadget(side):
    model = read_json(T1_B4 / side / "model.json")
    props = read_json(T1_B4 / side / "properties.json")

    roles = []

    for sw, data in sorted(model["Switches"].items()):
        init = data.get("InitialFlowTable", "zero")
        core_updates = non_bg_updates(data)

        if init != "zero" or core_updates:
            roles.append({
                "original_switch": sw,
                "initial": init,
                "core_updates": core_updates,
            })

    source_roles = []
    endpoint_roles = []
    core_roles = []

    for r in roles:
        init = r["initial"]
        updates = r["core_updates"]

        if init != "zero" and "(port = 1)" in init:
            source_roles.append(r)
        elif init != "zero":
            endpoint_roles.append(r)
        elif updates:
            core_roles.append(r)
        else:
            core_roles.append(r)

    # Include any role that combines init + updates conservatively.
    assigned = {id(r) for r in source_roles + endpoint_roles + core_roles}
    for r in roles:
        if id(r) not in assigned:
            core_roles.append(r)

    rec_core = {
        k: v for k, v in model.get("RecursiveVariables", {}).items()
        if k in CORE_CONTROLLERS
    }

    if sorted(rec_core.keys()) != sorted(CORE_CONTROLLERS):
        raise SystemExit(f"{side}: missing core recursive vars; got {sorted(rec_core.keys())}")

    return {
        "model": model,
        "properties": props,
        "source_roles": source_roles,
        "endpoint_roles": endpoint_roles,
        "core_roles": core_roles,
        "recursive_core": rec_core,
        "links": model["Links"],
    }

def clear_to_template_base(template):
    switches = {}

    for sw, old in template["Switches"].items():
        switches[sw] = {
            "InitialFlowTable": "zero",
            "DirectUpdates": bg_updates(old),
            "RequestedUpdates": [],
        }

    rec = {
        k: v for k, v in template.get("RecursiveVariables", {}).items()
        if k == "CBg"
    }

    controllers = ["CBg"] if "CBg" in rec else []

    return {
        "Switches": switches,
        "Links": template["Links"],
        "RecursiveVariables": rec,
        "Controllers": controllers,
    }

def topology_links(edges):
    links = []
    base = 300000
    i = 0
    for u, v in edges:
        p_uv = base + i
        p_vu = base + i + 1
        links.append(link(p_uv, p_vu))
        links.append(link(p_vu, p_uv))
        i += 2
    return union(links)

def empty_direct_model(asset):
    switches = {}
    for n in asset["nodes"]:
        switches[sw_name(n)] = {
            "InitialFlowTable": "zero",
            "DirectUpdates": [],
            "RequestedUpdates": [],
        }

    return {
        "Switches": switches,
        "Links": topology_links(asset["edges"]),
        "RecursiveVariables": {},
        "Controllers": [],
    }

def add_cbg_oplus(model, asset, exclude, k_bg):
    candidates = [sw_name(n) for n in asset["nodes"] if sw_name(n) not in exclude]
    selected = candidates[:k_bg]

    if len(selected) != k_bg:
        raise SystemExit(f"Only found {len(selected)} background switches, need {k_bg}")

    parts = []
    for i, sw in enumerate(selected, start=1):
        ch = f"upBg{i}"
        p_in = 9000 + 10 * i
        p_out = p_in + 1
        pol = term(p_in, p_out)

        model["Switches"][sw]["DirectUpdates"].append({
            "Channel": ch,
            "Policy": pol,
        })
        parts.append(f'({ch} ! "{pol}") ; CBg')

    model["RecursiveVariables"]["CBg"] = " o+ ".join(parts)
    model["Controllers"].append("CBg")

def apply_t1_gadget(base, gadget, topo):
    roles = role_switches_from_asset(topo)

    source_sw = roles["source_sw"]
    endpoint_sw = roles["endpoint_sw"]
    core_sws = roles["core_sws"]

    # Apply source-role initial tables.
    for r in gadget["source_roles"]:
        base["Switches"][source_sw]["InitialFlowTable"] = merge_table(base["Switches"][source_sw].get("InitialFlowTable", "zero"), r["initial"])
        for u in r["core_updates"]:
            base["Switches"][source_sw]["DirectUpdates"].append(u)

    # Apply endpoint-role initial tables.
    for r in gadget["endpoint_roles"]:
        base["Switches"][endpoint_sw]["InitialFlowTable"] = merge_table(base["Switches"][endpoint_sw].get("InitialFlowTable", "zero"), r["initial"])
        for u in r["core_updates"]:
            base["Switches"][endpoint_sw]["DirectUpdates"].append(u)

    # Apply each remaining core role to a distinct core switch if possible.
    if len(core_sws) < len(gadget["core_roles"]):
        raise SystemExit(f"{topo}: not enough core switches")

    core_mapping = []
    for r, sw in zip(gadget["core_roles"], core_sws):
        if r["initial"] != "zero":
            base["Switches"][sw]["InitialFlowTable"] = merge_table(base["Switches"][sw].get("InitialFlowTable", "zero"), r["initial"])
        for u in r["core_updates"]:
            base["Switches"][sw]["DirectUpdates"].append(u)
        core_mapping.append((r["original_switch"], sw))

    # Preserve exact symbolic links from known-good T1 gadget.
    base["Links"] = add_links(base["Links"], gadget["links"])

    # Preserve exact core recursive-variable semantics from T1.
    for k, v in gadget["recursive_core"].items():
        base["RecursiveVariables"][k] = v

    # Put core controllers first, then CBg.
    controllers = []
    for c in CORE_CONTROLLERS:
        if c in base["RecursiveVariables"]:
            controllers.append(c)
    if "CBg" in base["RecursiveVariables"]:
        controllers.append("CBg")
    base["Controllers"] = controllers

    return {
        "source_switch": source_sw,
        "endpoint_switch": endpoint_sw,
        "core_mapping": core_mapping,
        "core_switches_used": [sw for _, sw in core_mapping],
    }

def generate_template(k, topo, depth):
    src = ARCHIVE / "l7_failover_churn" / k / topo
    dst = ROOT / "b4_failover_cleanup_churn" / k / topo

    if not src.exists():
        raise SystemExit(f"Missing template: {src}")

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    for side in ["bad", "control"]:
        template = read_json(src / side / "model.json")
        gadget = extract_t1_gadget(side)
        model = clear_to_template_base(template)
        mapping = apply_t1_gadget(model, gadget, topo)

        write_json(dst / side / "model.json", model)
        write_json(dst / side / "properties.json", gadget["properties"])

    meta = {
        "paper_id": "B4",
        "name": f"b4_failover_cleanup_{k}_{topo}",
        "policy_class": "failover_cleanup_stale_path",
        "status": "generated_unvalidated",
        "template_or_direct": "archived_churn_template",
        "topology_id": topo,
        "translation_honesty": (
            "B4 failover-cleanup benchmark generated by preserving the exact locked K8/T1 "
            "B4 symbolic failover/cleanup semantics and scaling only topology host and background churn."
        ),
    }
    write_json(dst / "metadata.json", meta)

    print("=" * 100)
    print(f"GENERATED B4 TEMPLATE {k} {topo}")
    print("path:", dst)

def generate_geant():
    k, topo, depth, k_bg = GEANT_JOB
    dst = ROOT / "b4_failover_cleanup_churn" / k / topo

    roles = role_switches_from_asset(topo)
    asset = roles["asset"]

    if dst.exists():
        shutil.rmtree(dst)

    for side in ["bad", "control"]:
        gadget = extract_t1_gadget(side)
        model = empty_direct_model(asset)

        exclude = {roles["source_sw"], roles["endpoint_sw"]} | set(roles["core_sws"][:len(gadget["core_roles"])])
        add_cbg_oplus(model, asset, exclude, k_bg)

        mapping = apply_t1_gadget(model, gadget, topo)

        write_json(dst / side / "model.json", model)
        write_json(dst / side / "properties.json", gadget["properties"])

    write_json(dst / "metadata.json", {
        "paper_id": "B4",
        "name": f"b4_failover_cleanup_{k}_{topo}",
        "policy_class": "failover_cleanup_stale_path",
        "status": "generated_unvalidated",
        "template_or_direct": "direct_topology_zoo_asset",
        "topology_id": topo,
        "topology_source": asset["source"],
        "topology_stats": asset["stats"],
        "translation_honesty": (
            "B4 failover-cleanup benchmark generated directly from Topology Zoo Geant2012 "
            "while preserving the exact locked K8/T1 B4 symbolic failover/cleanup semantics."
        ),
    })

    print("=" * 100)
    print(f"GENERATED B4 DIRECT {k} {topo}")
    print("path:", dst)
    print("source switch:", roles["source_sw"])
    print("endpoint switch:", roles["endpoint_sw"])
    print("core candidates:", roles["core_sws"][:5])

if not T1_B4.exists():
    raise SystemExit(f"Missing locked B4/T1 source: {T1_B4}")

for k, topo, depth in JOBS_TEMPLATE:
    generate_template(k, topo, depth)

generate_geant()
