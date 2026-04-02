import os
import sqlite3
import json
import collections

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")
HTML_PATH = os.path.join(ENGINE_DIR, "render_exports", "map_2d_organism_2k.html")

def export_html():
    print(f"[*] Triệu hồi Cơ thể Hữu Cơ (Organism) gồm 2000 Hạt Xương Sống...")
    
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

    # Ép chuẩn 2000 Nodes (Top Hubs)
    top_hubs = degrees.most_common(2000)
    valid_nodes = {k for k, v in top_hubs}
    
    nodes = []
    edges = []

    # THE HEART: PETE
    nodes.append({
        "id": "GOD_NODE_PETE",
        "label": "PETE (Core)",
        "group": "system",
        "color": "#ffffff",
        "size": 60,
        "font": {"size": 35, "color": "#fff", "bold": True}
    })

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
        elif n_type == "class": color = "#33cc33"; size = 18
        elif n_type == "function": color = "#3399ff"; size = 12
        elif n_type == "method": color = "#9933ff"; size = 12
        elif n_type == "chunk": color = "#555555"; size = 6
        elif n_type.startswith("base_"): color = "#ffff66"; size = max(4, (degrees[n_id]**0.4))

        nodes.append({
            "id": n_id, 
            "label": label[:25] if degrees[n_id]>15 else "", 
            "group": n_type, 
            "color": color, 
            "size": size
        })
        
        # PETE Gravity to pull them into an organism
        edges.append({"source": "GOD_NODE_PETE", "target": n_id, "type": "PETE_GRAVITY"})

    # Real biological edges
    for e in raw_edges:
        if e[0] in valid_nodes and e[1] in valid_nodes:
            edges.append({"source": e[0], "target": e[1], "type": e[2]})

    html_content = f"""<!DOCTYPE html><html><head><title>Pete 2K Organism</title><script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script><style>#mynetwork{{width:100vw;height:100vh;background:#050508}}body{{margin:0;overflow:hidden}} #count{{position:absolute; top:20px; left:20px; color:#0f0; font-family:sans-serif; z-index:99;}} </style></head><body>
    <div id="count">MÔ PHỎNG SINH VẬT 2000 NODE.<br>Vật lý đang nhào nặn... Xin chờ vài giây để hiện hình hài cuối cùng.</div>
    <div id="mynetwork"></div><script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet({json.dumps(edges)}.map(e => ({{ 
        from: e.source, 
        to: e.target, 
        color: e.type==="PETE_GRAVITY"?"rgba(255,255,255,0.01)": (e.type==="FRAME"?"rgba(0,255,255,0.15)":"rgba(255,0,255,0.15)"), 
        arrows:"to", 
        hidden: e.type==="PETE_GRAVITY" ? true : false // CHỈ ẨN SỢI GRAVITY. HIỆN TOÀN BỘ SỢI NEURON.
    }})));
    
    var network = new vis.Network(document.getElementById('mynetwork'), {{nodes, edges}}, {{
        nodes: {{shape: 'dot', font: {{color: '#ccc', size: 10}}}},
        edges: {{width: 1, smooth: false}}, 
        physics: {{
            forceAtlas2Based: {{gravitationalConstant: -50, centralGravity: 0.01, springLength: 100, springConstant: 0.08}},
            solver: 'forceAtlas2Based',
            stabilization: {{iterations: 300}} // Cho phép ổn định hoàn toàn hình dạng
        }}
    }});
    network.on("stabilizationIterationsDone", () => {{
        document.getElementById("count").innerHTML = "SINH VẬT ĐÃ NHẬN DẠNG HOÀN TẤT. (2000 Trụ cột)";
        network.setOptions({{physics:false}});
    }});
    </script></body></html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"[+] Output: {HTML_PATH}")

if __name__ == "__main__": export_html()
