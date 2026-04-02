import os
import sqlite3
import json
import collections

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")
HTML_PATH = os.path.join(ENGINE_DIR, "render_exports", "map_2d_full_emergent.html")

def export_html():
    print(f"[*] Đang triệu hồi bản đồ HỮU CƠ TOÀN TẬP (~100.000 Nodes)...")
    
    conn = sqlite3.connect(DB_PATH, timeout=60)
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
                degrees[n_id] += 1; degrees[m] += 1
                raw_edges.append((n_id, m, "MEAN"))
            for f in json.loads(r[4]):
                degrees[n_id] += 1; degrees[f] += 1
                raw_edges.append((n_id, f, "FRAME"))

    nodes = []
    edges = []

    nodes.append({
        "id": "GOD_NODE_PETE",
        "label": "PETE (Core)",
        "group": "system",
        "color": "#ffffff",
        "size": 50,
        "font": {"size": 40, "color": "#fff", "bold": True}
    })

    # Đưa toàn bộ 100k+ Nodes vào (Full)
    for r in rows:
        n_id = r[0]
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
        if n_type == "file": color = "#ff4c4c"; size = 20
        elif n_type == "file_doc": color = "#ff9933"; size = 20
        elif n_type == "class": color = "#33cc33"; size = 15
        elif n_type == "function": color = "#3399ff"; size = 10
        elif n_type == "method": color = "#9933ff"; size = 10
        elif n_type == "chunk": color = "#555555"; size = 6
        elif n_type.startswith("base_"): color = "#ffff66"; size = max(4, (degrees[n_id]**0.4))

        nodes.append({
            "id": n_id, 
            "label": label[:15] if degrees[n_id]>30 else "", 
            "group": n_type, 
            "color": color, 
            "size": size
        })
        
        # PETE Hub to ALL
        edges.append({"from": "GOD_NODE_PETE", "to": n_id, "hidden": True})

    for e in raw_edges:
        edges.append({"from": e[0], "to": e[1], "hidden": True})

    html_content = f"""<!DOCTYPE html><html><head><title>Pete FULL Organic</title><script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script><style>#mynetwork{{width:100vw;height:100vh;background:#050508}}body{{margin:0;overflow:hidden}} #count{{position:absolute; top:20px; left:20px; color:#ff0; font-family:sans-serif; z-index:99;}} </style></head><body>
    <div id="count">Đang dùng CPU để nhào nặn Vô thức Hữu cơ cho toàn bộ {len(nodes)} Hạt.<br>Đã ngắt hoàn toàn vẽ Wire (Line) để cứu RAM.</div>
    <div id="mynetwork"></div><script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet({json.dumps(edges)});
    var network = new vis.Network(document.getElementById('mynetwork'), {{nodes, edges}}, {{
        nodes: {{shape: 'dot', font: {{color: '#ccc', size: 10}}}},
        edges: {{}},
        physics: {{
            barnesHut: {{gravitationalConstant: -10, centralGravity: 0.1, springLength: 80, springConstant: 0.04}},
            solver: 'barnesHut',
            stabilization: false // Cho phép xem thời gian thực quá trình nhào nặn mà không chờ crash
        }},
        interaction: {{ dragNodes: false }}
    }});
    </script></body></html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"[+] Output: {HTML_PATH}")

if __name__ == "__main__": export_html()
