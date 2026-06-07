#!/usr/bin/env python3
import json
import shutil
from pathlib import Path

ROOT = Path("benchmarks_comprehensive_topologies")
ASSET = ROOT / "_topology_assets" / "T3_geant2012.json"

TOPO = "T3_geant2012"
K = "K14"
DEPTH = 4
K_BG = 14

asset = json.loads(ASSET.read_text())

nodes = asset["nodes"]
edges = asset["edges"]
anchors = asset["default_anchors"]

source_node = anchors["source"]
dest_node = anchors["destination"]
waypoint_node = anchors["waypoint_on_diameter_path"]

def sw_name(node):
    return "SW" + "".join(c for c in str(node) if c.isdigit())

source_sw = sw_name(source_node)
waypoint_sw = sw_name(waypoint_node)
dest_sw = sw_name(dest_node)

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

def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n")

def topology_links():
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

def empty_model():
    switches = {}
    for n in nodes:
        switches[sw_name(n)] = {
            "InitialFlowTable": "zero",
            "DirectUpdates": [],
            "RequestedUpdates": []
        }

    return {
        "Switches": switches,
        "Links": union(topology_links()),
        "RecursiveVariables": {},
        "Controllers": []
    }

def add_links(model, extra_links):
    model["Links"] = union([model["Links"]] + extra_links)

def add_background_churn(model, exclude_switches):
    candidates = [sw_name(n) for n in nodes if sw_name(n) not in exclude_switches]
    selected = candidates[:K_BG]

    rec_parts = []

    for i, sw in enumerate(selected):
        ch = f"upBg{i}"
        p_in = 91000 + 2 * i
        p_out = 91000 + 2 * i + 1
        pol = term(p_in, p_out)

        model["Switches"][sw]["DirectUpdates"].append({
            "Channel": ch,
            "Policy": pol
        })

        rec_parts.append(f'({ch} ! "{pol}") ; CBg')

    model["RecursiveVariables"]["CBg"] = " + ".join(f"({part})" for part in rec_parts)
    model["Controllers"].append("CBg")

    return selected

def write_source_embedding(dst, encoding_key, encoding):
    src_dir = dst / "source"
    src_dir.mkdir(parents=True, exist_ok=True)
    write_json(src_dir / "churn_embedding.json", {
        "topology_id": TOPO,
        "source": asset["source"],
        "topology_stats": asset["stats"],
        "core_embedding": {
            "source_node": source_node,
            "waypoint_node": waypoint_node,
            "destination_node": dest_node,
            encoding_key: encoding,
        }
    })

# --------------------------------------------------------------------
# B1 waypoint-order
# --------------------------------------------------------------------

B1_SRC_UNINSPECTED = 2

B1_SRC_TO_WAYPOINT = 8501
B1_WAYPOINT_IN = 8502

B1_INSPECTED_TAG = 8503
B1_DEST_INSPECTED_IN = 8504
B1_DEST_OK_MARKER = 8505
B1_DEST_OK = 8506

B1_UNINSPECTED_TAG = 8510
B1_DEST_UNINSPECTED_IN = 8511
B1_DEST_BAD_MARKER = 8512
B1_DEST_BAD_UNINSPECTED = 8513

b1_ingress_update = term(B1_SRC_UNINSPECTED, B1_SRC_TO_WAYPOINT)
b1_waypoint_safe_update = term(B1_WAYPOINT_IN, B1_INSPECTED_TAG)
b1_waypoint_bad_initial = term(B1_WAYPOINT_IN, B1_UNINSPECTED_TAG)
b1_waypoint_control_initial = term(B1_WAYPOINT_IN, B1_INSPECTED_TAG)

b1_dest_table = union([
    term(B1_DEST_INSPECTED_IN, B1_DEST_OK_MARKER),
    term(B1_DEST_UNINSPECTED_IN, B1_DEST_BAD_MARKER),
])

b1_links = [
    link(B1_SRC_TO_WAYPOINT, B1_WAYPOINT_IN),
    link(B1_INSPECTED_TAG, B1_DEST_INSPECTED_IN),
    link(B1_UNINSPECTED_TAG, B1_DEST_UNINSPECTED_IN),
    link(B1_DEST_OK_MARKER, B1_DEST_OK),
    link(B1_DEST_BAD_MARKER, B1_DEST_BAD_UNINSPECTED),
]

b1_properties = {
    "Properties": {
        "CT->SW": {
            "Expression": f"(port={B1_SRC_UNINSPECTED}) . @Network . (port={B1_DEST_BAD_UNINSPECTED})",
            "AllowsPackets": False
        },
        "CT->SW<-CT": {
            "Expression": f"(port={B1_SRC_UNINSPECTED}) . @Network . (port={B1_DEST_BAD_UNINSPECTED})",
            "AllowsPackets": False
        },
        "CT->CT->SW": {
            "Expression": f"(port={B1_SRC_UNINSPECTED}) . @Network . (port={B1_DEST_BAD_UNINSPECTED})",
            "AllowsPackets": False
        }
    }
}

def make_b1(side):
    model = empty_model()
    bg = add_background_churn(model, {source_sw, waypoint_sw, dest_sw})

    waypoint_initial = b1_waypoint_bad_initial if side == "bad" else b1_waypoint_control_initial

    model["Switches"][source_sw]["DirectUpdates"].insert(0, {
        "Channel": "upIngress",
        "Policy": b1_ingress_update
    })

    model["Switches"][waypoint_sw]["InitialFlowTable"] = waypoint_initial
    model["Switches"][waypoint_sw]["DirectUpdates"].insert(0, {
        "Channel": "upWaypoint",
        "Policy": b1_waypoint_safe_update
    })

    model["Switches"][dest_sw]["InitialFlowTable"] = b1_dest_table

    add_links(model, b1_links)

    model["RecursiveVariables"]["CIngress"] = f'(upIngress ! "{b1_ingress_update}") ; CIngress'
    model["RecursiveVariables"]["CWaypoint"] = f'(upWaypoint ! "{b1_waypoint_safe_update}") ; CWaypoint'

    model["Controllers"] = ["CIngress", "CWaypoint"] + [
        c for c in model["Controllers"] if c not in {"CIngress", "CWaypoint"}
    ]

    return model

b1_dst = ROOT / "b1_waypoint_order_churn" / K / TOPO
if b1_dst.exists():
    shutil.rmtree(b1_dst)

write_json(b1_dst / "bad/model.json", make_b1("bad"))
write_json(b1_dst / "control/model.json", make_b1("control"))
write_json(b1_dst / "bad/properties.json", b1_properties)
write_json(b1_dst / "control/properties.json", b1_properties)

b1_encoding = {
    "source_node": source_node,
    "waypoint_node": waypoint_node,
    "destination_node": dest_node,
    "source_switch": source_sw,
    "waypoint_switch": waypoint_sw,
    "destination_switch": dest_sw,
    "source_uninspected_port": B1_SRC_UNINSPECTED,
    "ingress_update": b1_ingress_update,
    "bad_waypoint_initial": b1_waypoint_bad_initial,
    "control_waypoint_initial": b1_waypoint_control_initial,
    "waypoint_safe_update": b1_waypoint_safe_update,
    "destination_table": b1_dest_table,
    "destination_bad_uninspected_port": B1_DEST_BAD_UNINSPECTED,
    "checked_property": b1_properties["Properties"]["CT->SW"]["Expression"],
    "k_background": K_BG,
}

write_json(b1_dst / "metadata.json", {
    "paper_id": "B1",
    "name": f"b1_waypoint_order_{K}_{TOPO}",
    "policy_class": "waypoint_update_order_uninspected_destination",
    "status": "generated_unvalidated",
    "topology_id": TOPO,
    "topology_source": asset["source"],
    "topology_stats": asset["stats"],
    "translation_honesty": (
        "B1 waypoint-order benchmark generated directly from a Topology Zoo-derived topology asset. "
        "CIngress installs source forwarding; CWaypoint installs inspection. The faulty model initially "
        "forwards monitored traffic as uninspected; the control is safe from the start."
    ),
    "b1_waypoint_order_encoding": b1_encoding,
})

write_source_embedding(b1_dst, "b1_waypoint_order_encoding", b1_encoding)

# --------------------------------------------------------------------
# B2 forced-distinct route mapping
# --------------------------------------------------------------------

PREFIX_A = 1
PREFIX_B = 2

SRC_A_OUT = 8701
SRC_B_OUT = 8702

ROUTER_A_IN = 8711
ROUTER_B_IN = 8712

NEXT_HOP_A = 8721
NEXT_HOP_B = 8722

GW_A_IN = 8731
GW_B_IN = 8732

GW_A_MARKER = 8741
GW_B_MARKER = 8742

GW_A_ENDPOINT = 8751
GW_B_ENDPOINT = 8752

source_table = union([
    term(PREFIX_A, SRC_A_OUT),
    term(PREFIX_B, SRC_B_OUT),
])

route_bad_update = union([
    term(ROUTER_A_IN, NEXT_HOP_B),
    term(ROUTER_B_IN, NEXT_HOP_A),
])

route_control_update = union([
    term(ROUTER_A_IN, NEXT_HOP_A),
    term(ROUTER_B_IN, NEXT_HOP_B),
])

gateway_table = union([
    term(GW_A_IN, GW_A_MARKER),
    term(GW_B_IN, GW_B_MARKER),
])

b2_links = [
    link(SRC_A_OUT, ROUTER_A_IN),
    link(SRC_B_OUT, ROUTER_B_IN),
    link(NEXT_HOP_A, GW_A_IN),
    link(NEXT_HOP_B, GW_B_IN),
    link(GW_A_MARKER, GW_A_ENDPOINT),
    link(GW_B_MARKER, GW_B_ENDPOINT),
]

b2_properties = {
    "Properties": {
        "CT->SW": {
            "Expression": f"(port={PREFIX_A}) . @Network . (port={GW_B_ENDPOINT})",
            "AllowsPackets": False
        },
        "CT->SW<-CT": {
            "Expression": f"(port={PREFIX_A}) . @Network . (port={GW_B_ENDPOINT})",
            "AllowsPackets": False
        },
        "CT->CT->SW": {
            "Expression": f"(port={PREFIX_A}) . @Network . (port={GW_B_ENDPOINT})",
            "AllowsPackets": False
        }
    }
}

router_sw = waypoint_sw
gateway_sw = dest_sw

if len({source_sw, router_sw, gateway_sw}) != 3:
    raise SystemExit(f"B2 anchors not distinct: {source_sw}, {router_sw}, {gateway_sw}")

def make_b2(side):
    model = empty_model()
    bg = add_background_churn(model, {source_sw, router_sw, gateway_sw})

    route_update = route_bad_update if side == "bad" else route_control_update

    model["Switches"][source_sw]["InitialFlowTable"] = source_table
    model["Switches"][router_sw]["DirectUpdates"].insert(0, {
        "Channel": "upRoute",
        "Policy": route_update
    })
    model["Switches"][gateway_sw]["InitialFlowTable"] = gateway_table

    add_links(model, b2_links)

    model["RecursiveVariables"]["CRoute"] = f'(upRoute ! "{route_update}") ; CRoute'
    model["Controllers"] = ["CRoute"] + [c for c in model["Controllers"] if c != "CRoute"]

    return model

b2_dst = ROOT / "b2_route_mapping_forced_distinct" / K / TOPO
if b2_dst.exists():
    shutil.rmtree(b2_dst)

write_json(b2_dst / "bad/model.json", make_b2("bad"))
write_json(b2_dst / "control/model.json", make_b2("control"))
write_json(b2_dst / "bad/properties.json", b2_properties)
write_json(b2_dst / "control/properties.json", b2_properties)

b2_encoding = {
    "source_node": source_node,
    "router_node": waypoint_node,
    "gateway_node": dest_node,
    "source_switch": source_sw,
    "router_switch": router_sw,
    "gateway_switch": gateway_sw,
    "all_distinct": True,
    "prefix_a_port": PREFIX_A,
    "prefix_b_port": PREFIX_B,
    "source_table": source_table,
    "bad_route_update": route_bad_update,
    "control_route_update": route_control_update,
    "gateway_table": gateway_table,
    "gateway_a_endpoint": GW_A_ENDPOINT,
    "gateway_b_endpoint": GW_B_ENDPOINT,
    "checked_property": b2_properties["Properties"]["CT->SW"]["Expression"],
    "bad_path": f"{PREFIX_A} -> {SRC_A_OUT} -> {ROUTER_A_IN} -> {NEXT_HOP_B} -> {GW_B_IN} -> {GW_B_MARKER} -> {GW_B_ENDPOINT}",
    "control_path": f"{PREFIX_A} -> {SRC_A_OUT} -> {ROUTER_A_IN} -> {NEXT_HOP_A} -> {GW_A_IN} -> {GW_A_MARKER} -> {GW_A_ENDPOINT}",
    "k_background": K_BG,
}

write_json(b2_dst / "metadata.json", {
    "paper_id": "B2",
    "name": f"b2_route_mapping_forced_distinct_{K}_{TOPO}",
    "policy_class": "wrong_next_hop_route_mapping",
    "status": "generated_unvalidated",
    "topology_id": TOPO,
    "topology_source": asset["source"],
    "topology_stats": asset["stats"],
    "translation_honesty": (
        "B2 forced-distinct route-mapping benchmark generated directly from a Topology Zoo-derived topology asset. "
        "Source, router, and gateway are distinct switches. The faulty update maps Prefix A to Gateway B; "
        "the control maps Prefix A to Gateway A."
    ),
    "b2_route_mapping_encoding": b2_encoding,
})

write_source_embedding(b2_dst, "b2_route_mapping_encoding", b2_encoding)

print("=" * 88)
print("GENERATED T3_geant2012 B1/B2 K14")
print("=" * 88)
print("asset:", ASSET)
print("topology source:", asset["source"])
print("topology stats:", asset["stats"])
print("source:", source_node, source_sw)
print("waypoint/router:", waypoint_node, waypoint_sw)
print("destination/gateway:", dest_node, dest_sw)
print("background K:", K_BG)
print()
print("B1:", b1_dst)
print("B2:", b2_dst)
