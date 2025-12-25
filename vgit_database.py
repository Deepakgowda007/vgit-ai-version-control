import sqlite3
import os
import chromadb
import difflib

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
    
    # Create snapshots folder
    snap_path = os.path.join(VGIT_DIR, SNAPSHOTS_DIR)
    if not os.path.exists(snap_path):
        os.makedirs(snap_path)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, message TEXT, code_diff_file TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, snapshot_id TEXT, prompt_text TEXT, ai_response_text TEXT, embedding_id TEXT, FOREIGN KEY(snapshot_id) REFERENCES snapshots(id))''')
    conn.commit()
    conn.close()
    
    _ = get_chroma_client()
    print(f"✅ VGIT Initialized.")

def create_code_manifest(snapshot_id, project_root='.'):
    """Scans the project and saves a list of all current files."""
    snap_folder = os.path.join(VGIT_DIR, SNAPSHOTS_DIR)
    if not os.path.exists(snap_folder):
        os.makedirs(snap_folder)
    
    filename = f"{snapshot_id}.txt"
    filepath = os.path.join(snap_folder, filename)
    
    try:
        with open(filepath, "w") as f:
            f.write(f"VGIT Snapshot Manifest: {snapshot_id}\n")
            f.write("---------------------------------------\n")
            f.write("Tracked Files:\n")
            for root, dirs, files in os.walk(project_root):
                if '.vgit' in root or '.venv' in root or '.git' in root or '__pycache__' in root:
                    continue
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    f.write(f"- {rel_path}\n")
        return filename
    except Exception as e:
        print(f"❌ Error creating manifest: {e}")
        return "error_creating_manifest.txt"

def add_snapshot(snapshot_id, message, prompt_text, response_text):
    diff_file = create_code_manifest(snapshot_id)
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO snapshots (id, message, code_diff_file) VALUES (?, ?, ?)", 
                       (snapshot_id, message, diff_file))
        cursor.execute("INSERT INTO prompts (snapshot_id, prompt_text, ai_response_text) VALUES (?, ?, ?)", 
                       (snapshot_id, prompt_text, response_text))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Database Error: {e}")
        return False
    finally:
        conn.close()

def save_vector(snapshot_id, text, vector_list):
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="vgit_vectors")
        collection.add(ids=[snapshot_id], embeddings=[vector_list], documents=[text], metadatas=[{"type": "conversation"}])
        print(f"🧠 Vector saved to ChromaDB (ID: {snapshot_id[:8]})")
        return True
    except Exception as e:
        print(f"❌ Vector Error: {e}")
        return False

def query_vectors(query_vector, n_results=3):
    try:
        client = get_chroma_client()
        collection = client.get_collection(name="vgit_vectors")
        results = collection.query(query_embeddings=[query_vector], n_results=n_results)
        if results['ids']:
            return list(zip(results['ids'][0], results['distances'][0], results['documents'][0]))
        return []
    except Exception as e:
        print(f"❌ Query Error: {e}")
        return []

def get_snapshot_details(snapshot_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT s.timestamp, s.message, p.prompt_text, p.ai_response_text FROM snapshots s JOIN prompts p ON s.id = p.snapshot_id WHERE s.id = ?", (snapshot_id,))
        return cursor.fetchone()
    finally:
        conn.close()

# --- MISSING FUNCTIONS ADDED BELOW ---

def get_all_snapshots():
    """Returns a list of all snapshots ordered by timestamp (newest first)."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id, s.timestamp, s.message, p.prompt_text 
            FROM snapshots s
            JOIN prompts p ON s.id = p.snapshot_id
            ORDER BY s.timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"❌ Database Error: {e}")
        return []
    finally:
        conn.close()

def get_status(project_root='.'):
    """Compares current files with the last snapshot's manifest."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT code_diff_file FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            return {"status": "No snapshots yet."}
            
        last_manifest_file = row[0]
        manifest_path = os.path.join(VGIT_DIR, SNAPSHOTS_DIR, last_manifest_file)
        
        if not os.path.exists(manifest_path):
             return {"status": "Error: Manifest file missing."}

        tracked_files = set()
        with open(manifest_path, "r") as f:
            for line in f:
                if line.startswith("- "):
                    tracked_files.add(line.strip()[2:])

        current_files = set()
        for root, dirs, files in os.walk(project_root):
            if '.vgit' in root or '.venv' in root or '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                current_files.add(rel_path)
        
        new_files = current_files - tracked_files
        deleted_files = tracked_files - current_files
        
        return {
            "status": "Active",
            "new": list(new_files),
            "deleted": list(deleted_files),
            "total_tracked": len(tracked_files)
        }

    except sqlite3.Error as e:
        print(f"❌ Database Error: {e}")
        return {"status": "Error"}
    finally:
        conn.close()
