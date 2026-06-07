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

JOBS_TEMPLATE = [
    ("K12", "T2_nobel_eu", 4),
    ("K16", "T4_germany50", 4),
]

GEANT_JOB = ("K14", "T3_geant2012", 4, 14)

# Exact known-good B3/T1 symbolic semantics.
SLICE_A_IN = 1
SLICE_B_IN = 2

SRC_A_OUT = 8901
SRC_B_OUT = 8902

SLICE_A_PORT = 8911
SLICE_B_PORT = 8912

SLICE_A_FORWARD = 8921
SLICE_B_FORWARD = 8922

ENDPOINT_A_IN = 8931
ENDPOINT_B_IN = 8932

A_MARKER = 8941
B_MARKER = 8942

A_ENDPOINT = 8951
B_ENDPOINT = 8952

def read_json(p):
    return json.loads(Path(p).read_text())

def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n")

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

def add_links(existing, links):
    s = str(existing).strip()
    if s == "zero":
        return union(links)

    parts = [s] + links
    return union(parts)

def sw_name(node):
    return "SW" + "".join(c for c in str(node) if c.isdigit())

def load_asset(topo):
    return read_json(ASSETS / f"{topo}.json")

def anchors_from_asset(topo):
    asset = load_asset(topo)
    a = asset["default_anchors"]
    return {
        "asset": asset,
        "source_sw": sw_name(a["source"]),
        "slice_sw": sw_name(a["waypoint_on_diameter_path"]),
        "endpoint_sw": sw_name(a["destination"]),
        "source_node": a["source"],
        "slice_node": a["waypoint_on_diameter_path"],
        "endpoint_node": a["destination"],
    }

source_table = union([
    term(SLICE_A_IN, SRC_A_OUT),
    term(SLICE_B_IN, SRC_B_OUT),
])

slice_a_bad_update = term(SLICE_A_PORT, SLICE_B_FORWARD)
slice_a_control_update = term(SLICE_A_PORT, SLICE_A_FORWARD)
slice_b_update = term(SLICE_B_PORT, SLICE_B_FORWARD)

endpoint_table = union([
    term(ENDPOINT_A_IN, A_MARKER),
    term(ENDPOINT_B_IN, B_MARKER),
])

semantic_links = [
    link(SRC_A_OUT, SLICE_A_PORT),
    link(SRC_B_OUT, SLICE_B_PORT),
    link(SLICE_A_FORWARD, ENDPOINT_A_IN),
    link(SLICE_B_FORWARD, ENDPOINT_B_IN),
    link(A_MARKER, A_ENDPOINT),
    link(B_MARKER, B_ENDPOINT),
]

properties = {
    "Properties": {
        "CT->SW": {
            "Expression": f"(port={SLICE_A_IN}) . @Network . (port={B_ENDPOINT})",
            "AllowsPackets": False
        },
        "CT->SW<-CT": {
            "Expression": f"(port={SLICE_A_IN}) . @Network . (port={B_ENDPOINT})",
            "AllowsPackets": False
        },
        "CT->CT->SW": {
            "Expression": f"(port={SLICE_A_IN}) . @Network . (port={B_ENDPOINT})",
            "AllowsPackets": False
        }
    }
}

def make_template_model(template, side, source_sw, slice_sw, endpoint_sw):
    slice_a_update = slice_a_bad_update if side == "bad" else slice_a_control_update

    switches = {}

    for sw, old in template["Switches"].items():
        bg_updates = [
            u for u in old.get("DirectUpdates", [])
            if str(u.get("Channel", "")).startswith("upBg")
        ]

        switches[sw] = {
            "InitialFlowTable": "zero",
            "DirectUpdates": bg_updates,
            "RequestedUpdates": []
        }

    switches[source_sw]["InitialFlowTable"] = source_table
    switches[slice_sw]["DirectUpdates"].insert(
        0, {"Channel": "upSliceA", "Policy": slice_a_update}
    )
    switches[slice_sw]["DirectUpdates"].insert(
        1, {"Channel": "upSliceB", "Policy": slice_b_update}
    )
    switches[endpoint_sw]["InitialFlowTable"] = endpoint_table

    rec = {
        k: v for k, v in template.get("RecursiveVariables", {}).items()
        if k not in {"CSlice", "CSliceA", "CSliceB"}
    }

    rec["CSliceA"] = f'(upSliceA ! "{slice_a_update}") ; CSliceA'
    rec["CSliceB"] = f'(upSliceB ! "{slice_b_update}") ; CSliceB'

    controllers = [
        c for c in template.get("Controllers", [])
        if c not in {"CSlice", "CSliceA", "CSliceB"}
    ]
    controllers = ["CSliceA", "CSliceB"] + controllers

    return {
        "Switches": switches,
        "Links": add_links(template["Links"], semantic_links),
        "RecursiveVariables": rec,
        "Controllers": controllers,
    }

def write_metadata(dst, k, topo, anchors, template_or_direct):
    enc = {
        "source_node": anchors["source_node"],
        "slice_node": anchors["slice_node"],
        "endpoint_node": anchors["endpoint_node"],
        "source_switch": anchors["source_sw"],
        "slice_switch": anchors["slice_sw"],
        "endpoint_switch": anchors["endpoint_sw"],
        "all_distinct": len({anchors["source_sw"], anchors["slice_sw"], anchors["endpoint_sw"]}) == 3,
        "source_table": source_table,
        "slice_a_bad_update": slice_a_bad_update,
        "slice_a_control_update": slice_a_control_update,
        "slice_b_update": slice_b_update,
        "endpoint_table": endpoint_table,
        "checked_property": properties["Properties"]["CT->SW"]["Expression"],
        "bad_path": f"{SLICE_A_IN} -> {SRC_A_OUT} -> {SLICE_A_PORT} -> {SLICE_B_FORWARD} -> {ENDPOINT_B_IN} -> {B_MARKER} -> {B_ENDPOINT}",
        "control_path": f"{SLICE_A_IN} -> {SRC_A_OUT} -> {SLICE_A_PORT} -> {SLICE_A_FORWARD} -> {ENDPOINT_A_IN} -> {A_MARKER} -> {A_ENDPOINT}",
        "semantics_source": "exact_known_good_B3_T1_port_structure",
    }

    asset = anchors["asset"]

    write_json(dst / "metadata.json", {
        "paper_id": "B3",
        "name": f"b3_slice_isolation_twocontroller_{k}_{topo}",
        "policy_class": "cross_slice_leakage_two_controller",
        "status": "generated_unvalidated",
        "topology_id": topo,
        "topology_source": asset["source"],
        "topology_stats": asset["stats"],
        "template_or_direct": template_or_direct,
        "translation_honesty": (
            "B3 two-controller slice-isolation benchmark using the exact known-good T1 symbolic "
            "semantics: source classifier, shared slice-controller switch, endpoint switch, and "
            "property forbidding Slice A traffic from reaching the Slice B endpoint. Only the "
            "topology host and background churn scale are changed."
        ),
        "b3_slice_isolation_encoding": enc,
    })

def generate_template(k, topo, depth):
    src = ARCHIVE / "l5_slice_isolation_churn" / k / topo
    dst = ROOT / "b3_slice_isolation_twocontroller_churn" / k / topo

    if not src.exists():
        raise SystemExit(f"Missing template: {src}")

    anchors = anchors_from_asset(topo)
    source_sw = anchors["source_sw"]
    slice_sw = anchors["slice_sw"]
    endpoint_sw = anchors["endpoint_sw"]

    if len({source_sw, slice_sw, endpoint_sw}) != 3:
        raise SystemExit(f"Anchors not distinct for {topo}: {source_sw}, {slice_sw}, {endpoint_sw}")

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    template = read_json(src / "bad/model.json")

    write_json(dst / "bad/model.json", make_template_model(template, "bad", source_sw, slice_sw, endpoint_sw))
    write_json(dst / "control/model.json", make_template_model(template, "control", source_sw, slice_sw, endpoint_sw))
    write_json(dst / "bad/properties.json", properties)
    write_json(dst / "control/properties.json", properties)
    write_metadata(dst, k, topo, anchors, "archived_churn_template")

    print("=" * 100)
    print(f"GENERATED EXACT-B3 TEMPLATE {k} {topo}")
    print("path:", dst)
    print("source switch:", source_sw)
    print("slice switch:", slice_sw)
    print("endpoint switch:", endpoint_sw)
    print("property:", properties["Properties"]["CT->SW"]["Expression"])

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
    return links

def empty_direct_model(asset):
    switches = {}
    for n in asset["nodes"]:
        switches[sw_name(n)] = {
            "InitialFlowTable": "zero",
            "DirectUpdates": [],
            "RequestedUpdates": []
        }
    return {
        "Switches": switches,
        "Links": union(topology_links(asset["edges"])),
        "RecursiveVariables": {},
        "Controllers": []
    }

def add_cbg_oplus(model, asset, exclude, k_bg):
    candidates = [sw_name(n) for n in asset["nodes"] if sw_name(n) not in exclude]
    selected = candidates[:k_bg]

    parts = []
    for i, sw in enumerate(selected, start=1):
        ch = f"upBg{i}"
        p_in = 9000 + 10 * i
        p_out = p_in + 1
        pol = term(p_in, p_out)
        model["Switches"][sw]["DirectUpdates"].append({
            "Channel": ch,
            "Policy": pol
        })
        parts.append(f'({ch} ! "{pol}") ; CBg')

    model["RecursiveVariables"]["CBg"] = " o+ ".join(parts)
    model["Controllers"].append("CBg")

def make_direct_model(side, anchors, k_bg):
    asset = anchors["asset"]
    source_sw = anchors["source_sw"]
    slice_sw = anchors["slice_sw"]
    endpoint_sw = anchors["endpoint_sw"]

    slice_a_update = slice_a_bad_update if side == "bad" else slice_a_control_update

    model = empty_direct_model(asset)
    add_cbg_oplus(model, asset, {source_sw, slice_sw, endpoint_sw}, k_bg)

    model["Switches"][source_sw]["InitialFlowTable"] = source_table
    model["Switches"][slice_sw]["DirectUpdates"].insert(
        0, {"Channel": "upSliceA", "Policy": slice_a_update}
    )
    model["Switches"][slice_sw]["DirectUpdates"].insert(
        1, {"Channel": "upSliceB", "Policy": slice_b_update}
    )
    model["Switches"][endpoint_sw]["InitialFlowTable"] = endpoint_table

    model["Links"] = add_links(model["Links"], semantic_links)

    model["RecursiveVariables"]["CSliceA"] = f'(upSliceA ! "{slice_a_update}") ; CSliceA'
    model["RecursiveVariables"]["CSliceB"] = f'(upSliceB ! "{slice_b_update}") ; CSliceB'
    model["Controllers"] = ["CSliceA", "CSliceB"] + [
        c for c in model["Controllers"] if c not in {"CSliceA", "CSliceB"}
    ]

    return model

def generate_geant():
    k, topo, depth, k_bg = GEANT_JOB
    dst = ROOT / "b3_slice_isolation_twocontroller_churn" / k / topo

    anchors = anchors_from_asset(topo)

    if len({anchors["source_sw"], anchors["slice_sw"], anchors["endpoint_sw"]}) != 3:
        raise SystemExit(f"Anchors not distinct for {topo}")

    if dst.exists():
        shutil.rmtree(dst)

    write_json(dst / "bad/model.json", make_direct_model("bad", anchors, k_bg))
    write_json(dst / "control/model.json", make_direct_model("control", anchors, k_bg))
    write_json(dst / "bad/properties.json", properties)
    write_json(dst / "control/properties.json", properties)
    write_metadata(dst, k, topo, anchors, "direct_topology_zoo_asset")

    print("=" * 100)
    print(f"GENERATED EXACT-B3 DIRECT {k} {topo}")
    print("path:", dst)
    print("source switch:", anchors["source_sw"])
    print("slice switch:", anchors["slice_sw"])
    print("endpoint switch:", anchors["endpoint_sw"])
    print("property:", properties["Properties"]["CT->SW"]["Expression"])

for k, topo, depth in JOBS_TEMPLATE:
    generate_template(k, topo, depth)

generate_geant()
