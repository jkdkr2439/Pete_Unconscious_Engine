import os
import sqlite3
import json
import collections

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")
HTML_PATH = os.path.join(ENGINE_DIR, "render_exports", "map_3d.html")

def export_html():
    print(f"[*] Đang dựng mô hình không gian 3D...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, raw_content FROM fractal_nodes WHERE type LIKE 'base_%'")
    hash_to_label = {r[0]: r[1] for r in c.fetchall()}
    
    c.execute("SELECT id, type, name_nodes, mean_nodes, frame_nodes FROM fractal_nodes")
    rows = c.fetchall()

    degrees = collections.Counter()
    raw_edges = []
    
    for r in rows:
        if not r[1].startswith("base_"):
            for m in json.loads(r[3]):
                degrees[r[0]] += 1
                degrees[m] += 1
                raw_edges.append((r[0], m))
            for f in json.loads(r[4]):
                degrees[r[0]] += 1
                degrees[f] += 1
                raw_edges.append((r[0], f))

    top_hubs = degrees.most_common(3000)
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
                
        val = max(1, min((degrees[n_id] ** 0.5) * 2, 30))
        nodes.append({
            "id": n_id,
            "name": f"[{n_type}] {label[:30]} (Force: {degrees[n_id]})",
            "group": n_type,
            "val": val
        })

    for e in raw_edges:
        if e[0] in valid_nodes and e[1] in valid_nodes:
            edges.append({"source": e[0], "target": e[1]})

    html_content = f"""<!DOCTYPE html><html><head><title>Pete Unconscious 3D</title><style>body{{margin:0;background-color:#000;overflow:hidden;}}</style><script src="https://unpkg.com/3d-force-graph"></script></head><body><div id="3d-graph"></div><script>
    const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
        .graphData({json.dumps({"nodes": nodes, "links": edges})})
        .nodeLabel('name').nodeAutoColorBy('group').nodeVal('val')
        .linkColor(() => 'rgba(255,255,255,0.06)').linkWidth(0.2).backgroundColor('#02020a')
        .d3Force('charge', d3.forceManyBody().strength(-15)).d3Force('link', d3.forceLink().distance(20))
        .onNodeClick(node => {{
            const distRatio = 1 + 100/Math.hypot(node.x, node.y, node.z);
            Graph.cameraPosition({{ x: node.x*distRatio, y: node.y*distRatio, z: node.z*distRatio }}, node, 2000);
        }});
    let angle = 0; setInterval(() => {{ Graph.cameraPosition({{x: 600*Math.sin(angle), z: 600*Math.cos(angle)}}); angle += Math.PI/2000; }}, 20);
    </script></body></html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"[+] Output: {HTML_PATH}")

if __name__ == "__main__": export_html()
