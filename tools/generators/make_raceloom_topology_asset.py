#!/usr/bin/env python3
import json
import sys
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    raise SystemExit("This script needs networkx. Use: python3 -m pip install networkx")

if len(sys.argv) != 5:
    raise SystemExit("usage: make_raceloom_topology_asset.py INPUT.graphml TOPOLOGY_ID SOURCE_LABEL OUTPUT.json")

in_path = Path(sys.argv[1])
topology_id = sys.argv[2]
source_label = sys.argv[3]
out_path = Path(sys.argv[4])

G_raw = nx.read_graphml(in_path)
G = nx.Graph()

for n in G_raw.nodes():
    G.add_node(str(n))

for u, v in G_raw.edges():
    if str(u) != str(v):
        G.add_edge(str(u), str(v))

if not nx.is_connected(G):
    largest = max(nx.connected_components(G), key=len)
    G = G.subgraph(largest).copy()

old_nodes = sorted(G.nodes())
mapping = {old: f"n{i+1:03d}" for i, old in enumerate(old_nodes)}
G = nx.relabel_nodes(G, mapping)

nodes = sorted(G.nodes())
edges = sorted([sorted([u, v]) for u, v in G.edges()])

diameter = nx.diameter(G)
cycle_rank = G.number_of_edges() - G.number_of_nodes() + 1

all_pairs = dict(nx.all_pairs_shortest_path(G))
best_path = None
for u in nodes:
    for v in nodes:
        path = all_pairs[u][v]
        if best_path is None or len(path) > len(best_path):
            best_path = path

source = best_path[0]
destination = best_path[-1]
waypoint = best_path[len(best_path) // 2]

obj = {
    "topology_id": topology_id,
    "source": source_label,
    "nodes": nodes,
    "edges": edges,
    "stats": {
        "nodes": len(nodes),
        "edges": len(edges),
        "diameter": diameter,
        "cycle_rank": cycle_rank,
        "connected": True,
    },
    "node_label_mapping": {v: k for k, v in mapping.items()},
    "default_anchors": {
        "source": source,
        "destination": destination,
        "waypoint_on_diameter_path": waypoint,
        "diameter_path": best_path,
    },
}

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(obj, indent=2) + "\n")

print("Wrote:", out_path)
print("topology_id:", topology_id)
print("source:", source_label)
print("nodes:", len(nodes))
print("edges:", len(edges))
print("diameter:", diameter)
print("cycle_rank:", cycle_rank)
print("default source:", source)
print("default destination:", destination)
print("default waypoint:", waypoint)
print("diameter path:", " -> ".join(best_path))
