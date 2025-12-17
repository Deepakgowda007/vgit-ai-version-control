import argparse
import sys
import uuid
# Import the backend logic
from vgit_database import initialize_db, add_snapshot, save_vector

# --- GLOBAL AI MODEL INITIALIZATION ---
# This ensures 'model' is available to all functions
print("⏳ Loading AI Model (this may take a few seconds)...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ AI Model Loaded.")
except Exception as e:
    print(f"❌ Error loading AI model: {e}")
    sys.exit(1)
# --------------------------------------

def handle_init(args):
    """Initialize the VGIT repository."""
    print("Initializing VGIT...")
    initialize_db()

def handle_snapshot(args):
    """Capture a new snapshot of code + context."""
    # 1. Generate ID
    snapshot_id = str(uuid.uuid4())
    
    print(f"📸 Snapshotting: {args.message}")
    
    # 2. Prepare Text for Vectorization
    full_text = f"Prompt: {args.prompt}\nResponse: {args.response}"
    
    # 3. Generate Vector (Using the global 'model')
    print("🧠 Generating Vector Embedding...")
    try:
        vector = model.encode(full_text).tolist()
    except Exception as e:
        print(f"❌ Error generating vector: {e}")
        return

    # 4. Save to SQLite (Metadata)
    db_success = add_snapshot(snapshot_id, args.message, args.prompt, args.response)
    
    # 5. Save to ChromaDB (Vector)
    vec_success = save_vector(snapshot_id, full_text, vector)
    
    if db_success and vec_success:
        print("🎉 Snapshot Complete! (Metadata + Vector stored)")
    else:
        print("❌ Error saving snapshot.")

def handle_ask(args):
    """Search for past context."""
    print(f"🔍 Searching for: '{args.query}'")
    print("   (This feature is coming in Sprint Day 4)")

def main():
    parser = argparse.ArgumentParser(description="VGIT: Version Control for AI Context")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize a new .vgit repository")
    init_parser.set_defaults(func=handle_init)

    # Command: snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Save current state")
    snap_parser.add_argument("-m", "--message", required=True, help="Commit message")
    snap_parser.add_argument("-p", "--prompt", default="", help="The prompt you gave the AI")
    snap_parser.add_argument("-r", "--response", default="", help="The response the AI gave you")
    snap_parser.set_defaults(func=handle_snapshot)

    # Command: ask
    ask_parser = subparsers.add_parser("ask", help="Query your history")
    ask_parser.add_argument("query", help="The natural language question")
    ask_parser.set_defaults(func=handle_ask)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
