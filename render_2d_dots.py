import os
import sqlite3
import json
import collections
import random
import math

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")
HTML_PATH = os.path.join(ENGINE_DIR, "render_exports", "map_2d_full_dots.html")

def export_html():
    print(f"[*] Đang xuất FULL BẢN ĐỒ (Có thể lên tới 100k+ Nodes)...")
    print(f"[*] Chế độ: Tắt toàn bộ Liên kết Lực hấp dẫn (Chỉ vẽ Hạt) để cứu trình duyệt.")
    
    conn = sqlite3.connect(DB_PATH, timeout=60)
    c = conn.cursor()
    c.execute("SELECT id, raw_content FROM fractal_nodes WHERE type LIKE 'base_%'")
    hash_to_label = {r[0]: r[1] for r in c.fetchall()}
    
    c.execute("SELECT id, type, name_nodes, mean_nodes, frame_nodes FROM fractal_nodes")
    rows = c.fetchall()

    degrees = collections.Counter()
    
    # Tính độ lớn (độ mập) của các Node ẩn dưới nền
    for r in rows:
        n_id, n_type = r[0], r[1]
        if not n_type.startswith("base_"):
            for m in json.loads(r[3]):
                degrees[n_id] += 1; degrees[m] += 1
            for f in json.loads(r[4]):
                degrees[n_id] += 1; degrees[f] += 1

    nodes = []
    
    # Trải thiên hà ngẫu nhiên theo cụm (Semantic Galaxy)
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
                
        color = "#333"
        size = 3
        
        # Nhóm vị trí
        cx, cy = 0, 0
        if n_type == "file": color = "#ff4c4c"; size = 15; cx, cy = -4000, -4000
        elif n_type == "file_doc": color = "#ff9933"; size = 15; cx, cy = -4000, 4000
        elif n_type == "class": color = "#33cc33"; size = 10; cx, cy = 4000, -4000
        elif n_type == "function": color = "#3399ff"; size = 8; cx, cy = 0, -3000
        elif n_type == "method": color = "#9933ff"; size = 8; cx, cy = 3000, 0
        elif n_type == "chunk": color = "#555555"; size = 3; cx, cy = -2000, 2000
        elif n_type.startswith("base_"): color = "#ffff66"; size = 4 + (degrees[n_id]**0.4); cx, cy = 0, 0

        # Chuyển sang tọa độ cực (Polar Coordinates) để tạo hình Tròn (Galaxy) thay vì Hình Vuông
        spread = 20000 / max(1, (degrees[n_id]**0.5))
        radius = spread * (random.random() ** 0.8) # Mũ 0.8 để tụ tâm mạnh hơn, viền mỏng hơn
        angle = random.uniform(0, 2 * math.pi)
        
        nx = cx + radius * math.cos(angle)
        ny = cy + radius * math.sin(angle)

        nodes.append({
            "id": n_id, 
            "label": label[:15] if degrees[n_id] > 50 else "", 
            "group": n_type, 
            "color": color, 
            "size": size,
            "x": nx,
            "y": ny
        })

    html_content = f"""<!DOCTYPE html><html><head><title>Pete FULL SENSORIUM</title><script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script><style>#mynetwork{{width:100vw;height:100vh;background:#050505}}body{{margin:0;overflow:hidden}} #count{{position:absolute; top:20px; left:20px; color:#0f0; font-family:monospace; z-index:99;}} </style></head><body>
    <div id="count">TỔNG SỐ Node TRONG VÔ THỨC: {len(nodes)}<br>Đã ngắt dây liên kết để chống cháy RAM.</div>
    <div id="mynetwork"></div><script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet([]); // TRỐNG
    var network = new vis.Network(document.getElementById('mynetwork'), {{nodes, edges}}, {{
        nodes: {{shape: 'dot', font: {{color: '#ccc', size: 10}}}},
        edges: {{}}, 
        physics: false, // TẮT VẬT LÝ HOÀN TOÀN
        interaction: {{ dragNodes: false }}
    }});
    </script></body></html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"[+] Output: {HTML_PATH} | Total Nodes: {len(rows)}")

if __name__ == "__main__": export_html()
