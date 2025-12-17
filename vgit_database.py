import sqlite3
import os
import chromadb
from chromadb.config import Settings

VGIT_DIR = ".vgit"
DB_NAME = "vgit_metadata.db"
CHROMA_DIR = "chroma_db"

def get_db_path():
    return os.path.join(VGIT_DIR, DB_NAME)

def get_chroma_client():
    """Returns a persistent ChromaDB client."""
    chroma_path = os.path.join(VGIT_DIR, CHROMA_DIR)
    return chromadb.PersistentClient(path=chroma_path)

def initialize_db():
    """Creates the hidden directory, SQLite tables, and ChromaDB folder."""
    if not os.path.exists(VGIT_DIR):
        os.makedirs(VGIT_DIR)
        print(f"Created hidden directory: {VGIT_DIR}")
    
    # 1. Initialize SQLite
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message TEXT,
            code_diff_file TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT,
            prompt_text TEXT,
            ai_response_text TEXT,
            embedding_id TEXT,
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
        )
    ''')
    conn.commit()
    conn.close()
    
    # 2. Initialize ChromaDB (just by creating the client, it sets up folders)
    _ = get_chroma_client()
    
    print(f"✅ Database & Vector Store initialized in {VGIT_DIR}")

def add_snapshot(snapshot_id, message, prompt_text, response_text):
    """Inserts metadata into SQLite."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO snapshots (id, message, code_diff_file) VALUES (?, ?, ?)", 
                       (snapshot_id, message, "placeholder_diff.txt"))
        
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
    """Saves the vector embedding to ChromaDB."""
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="vgit_vectors")
        
        collection.add(
            ids=[snapshot_id],
            embeddings=[vector_list],
            documents=[text],
            metadatas=[{"type": "conversation"}]
        )
        print(f"🧠 Vector saved to ChromaDB (ID: {snapshot_id[:8]})")
        return True
    except Exception as e:
        print(f"❌ Vector Error: {e}")
        return False
