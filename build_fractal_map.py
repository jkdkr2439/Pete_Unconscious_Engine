import os
import sys
import ast
import json
import sqlite3
import re
import hashlib

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.dirname(ENGINE_DIR) # Go up one level to Pete_All_Versions
DB_PATH = os.path.join(ENGINE_DIR, "data", "pete_fieldmap.db")

target_folder_name = sys.argv[1] if len(sys.argv) > 1 else "v0.1_Origin"
TARGET_PATH = os.path.join(PROJECTS_DIR, target_folder_name)

base_nodes_cache = {}

def get_base_node(value, type_str):
    k = f"{type_str}:{value}"
    if k in base_nodes_cache: return base_nodes_cache[k]["id"]
    node_id = "0x" + hashlib.md5(f"BASE:{k}".encode()).hexdigest()[:12]
    base_nodes_cache[k] = {"id": node_id, "type": f"base_{type_str}", "value": value}
    return node_id

def collapse_hash(m_list, f_list):
    content = json.dumps({"M": sorted(m_list), "F": sorted(f_list)})
    return "0x" + hashlib.md5(content.encode()).hexdigest()[:12]

class FractalNode:
    def __init__(self, node_id, type_str, n_list, m_list, f_list, raw_content=""):
        self.id = node_id
        self.type = type_str
        self.name_nodes = n_list
        self.mean_nodes = m_list
        self.frame_nodes = f_list
        self.raw_content = raw_content

    def insert_to_db(self, cursor):
        cursor.execute('''
            INSERT OR IGNORE INTO fractal_nodes (id, type, name_nodes, mean_nodes, frame_nodes, raw_content)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.id, self.type,
            json.dumps(self.name_nodes),
            json.dumps(self.mean_nodes),
            json.dumps(self.frame_nodes),
            self.raw_content
        ))

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fractal_nodes (
            id TEXT PRIMARY KEY,
            type TEXT,
            name_nodes TEXT,
            mean_nodes TEXT,
            frame_nodes TEXT,
            raw_content TEXT
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_type ON fractal_nodes (type)')
    conn.commit()
    return conn, c

def extract_meaning_from_ast(ast_node):
    mean_hashes = set()
    for child in ast.walk(ast_node):
        if isinstance(child, ast.Name): mean_hashes.add(get_base_node(child.id, "var"))
        elif isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name): mean_hashes.add(get_base_node(child.func.id, "call"))
            elif isinstance(child.func, ast.Attribute): mean_hashes.add(get_base_node(child.func.attr, "call"))
    return list(mean_hashes)

def parse_python_file(file_path, file_frame_str, cursor):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception: return

    f_frame_id = get_base_node(file_frame_str, "file_path")
    file_m_list = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            c_f = [f_frame_id]
            c_m = []
            c_n_id = get_base_node(node.name, "class_name")
            c_n = [c_n_id]
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    m_f = [c_n_id]
                    m_n = [get_base_node(child.name, "method_name")]
                    m_m = extract_meaning_from_ast(child)
                    m_id = collapse_hash(m_m, m_f)
                    c_m.append(m_id)
                    FractalNode(m_id, "method", m_n, m_m, m_f, ast.unparse(child)).insert_to_db(cursor)
            c_id = collapse_hash(c_m, c_f)
            file_m_list.append(c_id)
            FractalNode(c_id, "class", c_n, c_m, c_f, ast.unparse(node)).insert_to_db(cursor)

        elif isinstance(node, ast.FunctionDef) and node in tree.body:
            f_f = [f_frame_id]
            f_n = [get_base_node(node.name, "function_name")]
            f_m = extract_meaning_from_ast(node)
            f_id = collapse_hash(f_m, f_f)
            file_m_list.append(f_id)
            FractalNode(f_id, "function", f_n, f_m, f_f, ast.unparse(node)).insert_to_db(cursor)

    file_f = [get_base_node(f"project:{target_folder_name}", "project")]
    file_n = [get_base_node(os.path.basename(file_path), "file_name")]
    true_file_id = collapse_hash(file_m_list, file_f)
    FractalNode(true_file_id, "file", file_n, file_m_list, file_f, "").insert_to_db(cursor)


def parse_text_file(file_path, file_frame_str, cursor):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception: return

    f_frame_id = get_base_node(file_frame_str, "file_path")
    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
    
    file_m_list = []
    for i, p in enumerate(paragraphs):
        c_f = [f_frame_id]
        c_n = [get_base_node(f"chunk:{i}", "chunk_name")]
        words = re.findall(r'\b[a-zA-Z_]{4,15}\b', p.lower())
        stop = {"this", "that", "with", "from", "then", "when"}
        c_m = []
        for w in set(words):
            if w not in stop: c_m.append(get_base_node(w, "word"))
        c_id = collapse_hash(c_m, c_f)
        file_m_list.append(c_id)
        FractalNode(c_id, "chunk", c_n, c_m, c_f, p).insert_to_db(cursor)

    file_f = [get_base_node(f"project:{target_folder_name}", "project")]
    file_n = [get_base_node(os.path.basename(file_path), "file_name")]
    true_file_id = collapse_hash(file_m_list, file_f)
    FractalNode(true_file_id, "file_doc", file_n, file_m_list, file_f, "").insert_to_db(cursor)

def main():
    print(f"[*] INGESTING [{target_folder_name}] into Semantic Map...")
    if not os.path.exists(TARGET_PATH):
        print(f"[-] Source directory {TARGET_PATH} not found!")
        return

    conn, c = setup_db()
    
    for root, dirs, files in os.walk(TARGET_PATH):
        for f in files:
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, TARGET_PATH).replace("\\", "/")
            if f.endswith(".py"): parse_python_file(filepath, rel_path, c)
            elif f.endswith((".txt", ".md", ".tex", ".csv", ".json")): parse_text_file(filepath, rel_path, c)

    for v in base_nodes_cache.values():
        FractalNode(v["id"], v["type"], [], [], [], v["value"]).insert_to_db(c)

    conn.commit()
    c.execute("SELECT count(*) FROM fractal_nodes")
    print(f"[+] DONE! Total Nodes in DB: {c.fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    main()
