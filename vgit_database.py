import sqlite3
import os
import chromadb

# --- CONFIGURATION ---
VGIT_DIR = ".vgit"
DB_NAME = "vgit_metadata.db"
CHROMA_DIR = "chroma_db"
SNAPSHOTS_DIR = "snapshots"

def get_db_path():
    return os.path.join(VGIT_DIR, DB_NAME)

def get_chroma_client():
    chroma_path = os.path.join(VGIT_DIR, CHROMA_DIR)
    return chromadb.PersistentClient(path=chroma_path)

def initialize_db():
    if not os.path.exists(VGIT_DIR):
        os.makedirs(VGIT_DIR)
    
    snap_path = os.path.join(VGIT_DIR, SNAPSHOTS_DIR)
    if not os.path.exists(snap_path):
        os.makedirs(snap_path)

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS snapshots (
        id TEXT PRIMARY KEY, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
        message TEXT, 
        code_diff_file TEXT,
        task_type TEXT DEFAULT 'feat',
        is_stable INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        snapshot_id TEXT, 
        prompt_text TEXT, 
        ai_response_text TEXT, 
        embedding_id TEXT, 
        FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
    )''')
    
    # Robust Migration
    cursor.execute("PRAGMA table_info(snapshots)")
    columns = [info[1] for info in cursor.fetchall()]
    if "task_type" not in columns:
        cursor.execute("ALTER TABLE snapshots ADD COLUMN task_type TEXT DEFAULT 'feat'")
    if "is_stable" not in columns:
        cursor.execute("ALTER TABLE snapshots ADD COLUMN is_stable INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
    _ = get_chroma_client()
    print(f"✅ vGit Engine Ready.")

def create_code_manifest(snapshot_id, project_root='.'):
    filename = f"{snapshot_id}.txt"
    filepath = os.path.join(VGIT_DIR, SNAPSHOTS_DIR, filename)
    try:
        with open(filepath, "w") as f:
            for root, dirs, files in os.walk(project_root):
                if any(x in root for x in ['.vgit', '.venv', '.git', '__pycache__']):
                    continue
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    f.write(f"- {rel_path}\n")
        return filename
    except Exception as e:
        return f"error_{e}.txt"

def add_snapshot(snapshot_id, message, prompt, response, task_type="feat", is_stable=0):
    diff_file = create_code_manifest(snapshot_id)
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO snapshots (id, message, code_diff_file, task_type, is_stable) VALUES (?, ?, ?, ?, ?)", 
                       (snapshot_id, message, diff_file, task_type, is_stable))
        cursor.execute("INSERT INTO prompts (snapshot_id, prompt_text, ai_response_text) VALUES (?, ?, ?)", 
                       (snapshot_id, prompt, response))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ DB Error: {e}")
        return False
    finally:
        conn.close()

def save_vector(snapshot_id, text, vector_list):
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="vgit_vectors")
        collection.add(ids=[snapshot_id], embeddings=[vector_list], documents=[text])
        return True
    except:
        return False

def query_vectors(query_vector, n_results=3):
    try:
        client = get_chroma_client()
        collection = client.get_collection(name="vgit_vectors")
        results = collection.query(query_embeddings=[query_vector], n_results=n_results)
        return list(zip(results['ids'][0], results['distances'][0], results['documents'][0])) if results['ids'] else []
    except:
        return []

def get_snapshot_details(snapshot_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        # Use COALESCE to handle NULL values for old data
        cursor.execute("""
            SELECT s.timestamp, s.message, p.prompt_text, p.ai_response_text, 
                   COALESCE(s.task_type, 'feat'), COALESCE(s.is_stable, 0) 
            FROM snapshots s 
            JOIN prompts p ON s.id = p.snapshot_id 
            WHERE s.id LIKE ?
        """, (f"{snapshot_id}%",))
        return cursor.fetchone()
    finally:
        conn.close()

def get_all_snapshots():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        # Use COALESCE to handle NULL values for old data
        cursor.execute("""
            SELECT s.id, s.timestamp, s.message, 
                   COALESCE(s.task_type, 'feat'), COALESCE(s.is_stable, 0) 
            FROM snapshots s 
            ORDER BY s.timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()

def get_manifest_content(snapshot_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM snapshots WHERE id LIKE ?", (f"{snapshot_id}%",))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    
    full_id = row[0]
    filepath = os.path.join(VGIT_DIR, SNAPSHOTS_DIR, f"{full_id}.txt")
    if not os.path.exists(filepath): return None
    
    with open(filepath, "r") as f:
        return [line.strip()[2:] for line in f if line.strip().startswith("- ")]

def get_status():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT code_diff_file FROM snapshots ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    
    manifest_path = os.path.join(VGIT_DIR, SNAPSHOTS_DIR, row[0])
    if not os.path.exists(manifest_path): return None

    with open(manifest_path, "r") as f:
        tracked = {line.strip()[2:] for line in f if line.strip().startswith("- ")}

    current = set()
    for root, dirs, files in os.walk('.'):
        if any(x in root for x in ['.vgit', '.venv', '.git', '__pycache__']): continue
        for file in files:
            current.add(os.path.relpath(os.path.join(root, file), '.'))

    return {"new": list(current - tracked), "deleted": list(tracked - current), "total": len(tracked)}
