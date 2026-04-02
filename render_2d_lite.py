import os
import sqlite3
import json
import collections

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")
HTML_PATH = os.path.join(ENGINE_DIR, "render_exports", "map_2d_lite.html")

MIN_DEGREE = 5 

def export_html():
    print(f"[*] Đang nén Bản đồ xuống phiên bản Lite 2D (Top 2000)...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, raw_content FROM fractal_nodes WHERE type LIKE 'base_%'")
    hash_to_label = {r[0]: r[1] for r in c.fetchall()}
    c.execute("SELECT id, type, name_nodes, mean_nodes, frame_nodes FROM fractal_nodes")
    rows = c.fetchall()

    degrees = collections.Counter()
    raw_edges = []
    
    for r in rows:
        n_id, n_type = r[0], r[1]
        if not n_type.startswith("base_"):
            for m in json.loads(r[3]):
                degrees[n_id] += 1
                degrees[m] += 1
                raw_edges.append((n_id, m, "MEAN"))
            for f in json.loads(r[4]):
                degrees[n_id] += 1
                degrees[f] += 1
                raw_edges.append((n_id, f, "FRAME"))

    top_hubs = degrees.most_common(2000)
    valid_nodes = {k for k, v in top_hubs}
    nodes, edges = [], []

    for r in rows:
        n_id = r[0]
        if n_id not in valid_nodes: continue
        n_type = r[1]
        label = ""
        if n_type.startswith("base_"): label = hash_to_label.get(n_id, n_id)
        else:
            try:
                nh = json.loads(r[2])
                if nh: label = hash_to_label.get(nh[0], "")
            except: pass
                
        color = "#444"
        size = 5
        if n_type == "file": color = "#ff4c4c"; size = 25
        elif n_type == "file_doc": color = "#ff9933"; size = 25
        elif n_type == "class": color = "#33cc33"; size = 20
        elif n_type == "function": color = "#3399ff"; size = 15
        elif n_type == "method": color = "#9933ff"; size = 15
        elif n_type == "chunk": color = "#555555"; size = 7
        elif n_type.startswith("base_"): color = "#ffff66"; size = 3

        nodes.append({"id": n_id, "label": label[:30], "group": n_type, "color": color, "size": size, "value": degrees[n_id]})

    for e in raw_edges:
        if e[0] in valid_nodes and e[1] in valid_nodes: edges.append({"source": e[0], "target": e[1], "type": e[2]})

    html_content = f"""<!DOCTYPE html><html><head><title>Pete LITE</title><script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script><style>#mynetwork{{width:100vw;height:100vh;background:#080808}}body{{margin:0;overflow:hidden}}</style></head><body>
    <div id="mynetwork"></div><script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet({json.dumps(edges)}.map(e => ({{ from: e.source, to: e.target, color: e.type==="FRAME"?"rgba(0,255,255,0.08)":"rgba(255,0,255,0.08)", arrows:"to" }})));
    var network = new vis.Network(document.getElementById('mynetwork'), {{nodes, edges}}, {{
        nodes: {{shape: 'dot', font: {{color: '#ccc', size: 10}}, scaling: {{min: 3, max: 30}}}},
        edges: {{width: 1, smooth: false}}, 
        physics: {{forceAtlas2Based: {{gravitationalConstant: -30}}, solver: 'forceAtlas2Based', stabilization: {{iterations: 150}}}}
    }});
    network.on("stabilizationIterationsDone", () => network.setOptions({{physics:false}}));
    </script></body></html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"[+] Output: {HTML_PATH}")

if __name__ == "__main__": export_html()
