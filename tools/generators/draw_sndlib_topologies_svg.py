#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path

ROOT = Path.cwd()
ASSET_DIR = ROOT / "benchmarks_comprehensive_topologies" / "_topology_assets"
OUT_DIR = ROOT / "benchmarks_comprehensive_topologies" / "topology_graphs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOPOLOGIES = [
    ("T1_atlanta", "SNDlib Atlanta"),
    ("T2_nobel_eu", "SNDlib Nobel-EU"),
    ("T3_cost266", "SNDlib Cost266"),
    ("T4_germany50", "SNDlib Germany50"),
]

WIDTH = 1200
HEIGHT = 900
MARGIN = 90

def load_topology(tid):
    p = ASSET_DIR / f"{tid}.json"
    if not p.exists():
        raise SystemExit(f"Missing topology file: {p}")
    return json.loads(p.read_text())

def normalize_edges(edges):
    out = []
    for e in edges:
        if isinstance(e, dict):
            u = e.get("source") or e.get("u") or e.get("from")
            v = e.get("target") or e.get("v") or e.get("to")
        else:
            u, v = e[0], e[1]
        out.append((str(u), str(v)))
    return sorted(set(tuple(sorted((u, v))) for u, v in out))

def force_layout(nodes, edges, seed=7, iterations=900):
    random.seed(seed)
    n = len(nodes)

    # Start on a circle, deterministic by node name.
    pos = {}
    for i, node in enumerate(sorted(nodes)):
        angle = 2 * math.pi * i / max(n, 1)
        r = min(WIDTH, HEIGHT) * 0.32
        pos[node] = [
            WIDTH / 2 + r * math.cos(angle) + random.uniform(-25, 25),
            HEIGHT / 2 + r * math.sin(angle) + random.uniform(-25, 25),
        ]

    area = WIDTH * HEIGHT
    k = math.sqrt(area / max(n, 1)) * 0.65

    edge_set = [(u, v) for u, v in edges if u in pos and v in pos]

    temp = WIDTH / 7

    for it in range(iterations):
        disp = {node: [0.0, 0.0] for node in nodes}

        # Repulsion
        sorted_nodes = sorted(nodes)
        for i, v in enumerate(sorted_nodes):
            for u in sorted_nodes[i+1:]:
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                dist = math.hypot(dx, dy) + 0.01
                force = (k * k) / dist
                fx = dx / dist * force
                fy = dy / dist * force
                disp[v][0] += fx
                disp[v][1] += fy
                disp[u][0] -= fx
                disp[u][1] -= fy

        # Attraction
        for v, u in edge_set:
            dx = pos[v][0] - pos[u][0]
            dy = pos[v][1] - pos[u][1]
            dist = math.hypot(dx, dy) + 0.01
            force = (dist * dist) / k
            fx = dx / dist * force
            fy = dy / dist * force
            disp[v][0] -= fx
            disp[v][1] -= fy
            disp[u][0] += fx
            disp[u][1] += fy

        # Update with cooling
        for v in nodes:
            dx, dy = disp[v]
            d = math.hypot(dx, dy)
            if d > 0:
                pos[v][0] += dx / d * min(d, temp)
                pos[v][1] += dy / d * min(d, temp)

            pos[v][0] = min(WIDTH - MARGIN, max(MARGIN, pos[v][0]))
            pos[v][1] = min(HEIGHT - MARGIN, max(MARGIN + 35, pos[v][1]))

        temp *= 0.995

    # Normalize to margins.
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    for v in nodes:
        x, y = pos[v]
        if maxx > minx:
            x = MARGIN + (x - minx) / (maxx - minx) * (WIDTH - 2*MARGIN)
        if maxy > miny:
            y = MARGIN + 45 + (y - miny) / (maxy - miny) * (HEIGHT - 2*MARGIN - 45)
        pos[v] = [x, y]

    return pos

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def write_svg(tid, title, topo):
    nodes = [str(n) for n in topo["nodes"]]
    edges = normalize_edges(topo["edges"])
    stats = topo.get("stats", {})
    anchors = topo.get("default_anchors", {})

    pos = force_layout(nodes, edges, seed=abs(hash(tid)) % 10000)

    source = anchors.get("source")
    dest = anchors.get("destination")
    waypoint = anchors.get("waypoint_on_diameter_path")

    degree = {n: 0 for n in nodes}
    for u, v in edges:
        degree[u] += 1
        degree[v] += 1

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">''')
    svg.append('''<rect width="100%" height="100%" fill="white"/>''')

    svg.append(f'''<text x="40" y="42" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#111">{esc(title)}</text>''')
    svg.append(f'''<text x="40" y="72" font-family="Arial, sans-serif" font-size="16" fill="#444">id: {esc(tid)} · nodes: {len(nodes)} · edges: {len(edges)} · diameter: {esc(stats.get("diameter", "?"))} · cycle rank: {esc(stats.get("cycle_rank", "?"))}</text>''')

    legend_y = 104
    svg.append(f'''<circle cx="45" cy="{legend_y}" r="8" fill="#111"/><text x="62" y="{legend_y+5}" font-family="Arial" font-size="14" fill="#333">ordinary node</text>''')
    svg.append(f'''<circle cx="190" cy="{legend_y}" r="9" fill="#2b6cb0"/><text x="207" y="{legend_y+5}" font-family="Arial" font-size="14" fill="#333">source</text>''')
    svg.append(f'''<circle cx="305" cy="{legend_y}" r="9" fill="#2f855a"/><text x="322" y="{legend_y+5}" font-family="Arial" font-size="14" fill="#333">destination</text>''')
    svg.append(f'''<circle cx="455" cy="{legend_y}" r="9" fill="#b7791f"/><text x="472" y="{legend_y+5}" font-family="Arial" font-size="14" fill="#333">waypoint</text>''')

    # Edges
    for u, v in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        svg.append(f'''<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#9aa0a6" stroke-width="2" opacity="0.72"/>''')

    # Nodes
    for n in sorted(nodes):
        x, y = pos[n]
        r = 10 + min(7, degree[n] * 1.4)

        fill = "#111"
        if n == source:
            fill = "#2b6cb0"
        elif n == dest:
            fill = "#2f855a"
        elif n == waypoint:
            fill = "#b7791f"

        svg.append(f'''<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="white" stroke-width="3"/>''')
        svg.append(f'''<text x="{x:.1f}" y="{y-r-7:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="600" fill="#111">{esc(n)}</text>''')

    if anchors:
        text = f"default anchors: source={source}, destination={dest}, waypoint={waypoint}"
        svg.append(f'''<text x="40" y="{HEIGHT-32}" font-family="Arial, sans-serif" font-size="15" fill="#444">{esc(text)}</text>''')

    svg.append("</svg>")

    out = OUT_DIR / f"{tid}.svg"
    out.write_text("\n".join(svg))
    print("Wrote", out)

def write_dot(tid, title, topo):
    nodes = [str(n) for n in topo["nodes"]]
    edges = normalize_edges(topo["edges"])
    anchors = topo.get("default_anchors", {})

    source = anchors.get("source")
    dest = anchors.get("destination")
    waypoint = anchors.get("waypoint_on_diameter_path")

    lines = []
    lines.append(f'graph "{tid}" {{')
    lines.append('  graph [layout=neato, overlap=false, splines=true];')
    lines.append('  node [shape=circle, style=filled, fillcolor=white, fontname="Arial"];')
    lines.append(f'  label="{title}";')
    lines.append('  labelloc="t";')

    for n in nodes:
        color = "black"
        fill = "white"
        if n == source:
            fill = "lightblue"
        elif n == dest:
            fill = "lightgreen"
        elif n == waypoint:
            fill = "orange"
        lines.append(f'  "{n}" [fillcolor="{fill}", color="{color}"];')

    for u, v in edges:
        lines.append(f'  "{u}" -- "{v}";')

    lines.append("}")
    out = OUT_DIR / f"{tid}.dot"
    out.write_text("\n".join(lines))
    print("Wrote", out)

def main():
    for tid, title in TOPOLOGIES:
        topo = load_topology(tid)
        write_svg(tid, title, topo)
        write_dot(tid, title, topo)

    # Index page
    index = OUT_DIR / "index.html"
    body = ['<!doctype html><html><head><meta charset="utf-8"><title>RaceLoom SNDlib Topologies</title></head><body style="font-family:Arial,sans-serif">']
    body.append("<h1>RaceLoom SNDlib topology graphs</h1>")
    for tid, title in TOPOLOGIES:
        body.append(f'<h2>{esc(title)} — {esc(tid)}</h2>')
        body.append(f'<img src="{tid}.svg" style="max-width:100%;border:1px solid #ddd">')
    body.append("</body></html>")
    index.write_text("\n".join(body))
    print("Wrote", index)

if __name__ == "__main__":
    main()
