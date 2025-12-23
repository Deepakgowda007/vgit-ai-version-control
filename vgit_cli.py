import argparse
import sys
import uuid
from vgit_database import initialize_db, add_snapshot, save_vector, query_vectors, get_snapshot_details

print("⏳ Loading AI Model...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ AI Model Loaded.")
except Exception as e:
    print(f"❌ Error loading AI model: {e}")
    sys.exit(1)

def handle_init(args):
    print("Initializing VGIT...")
    initialize_db()

def handle_snapshot(args):
    snapshot_id = str(uuid.uuid4())
    print(f"📸 Snapshotting: {args.message}")
    
    full_text = f"Prompt: {args.prompt}\nResponse: {args.response}"
    
    print("🧠 Generating Vector Embedding...")
    try:
        vector = model.encode(full_text).tolist()
    except Exception as e:
        print(f"❌ Error generating vector: {e}")
        return

    db_success = add_snapshot(snapshot_id, args.message, args.prompt, args.response)
    vec_success = save_vector(snapshot_id, full_text, vector)
    
    if db_success and vec_success:
        print("🎉 Snapshot Complete! (Metadata + Vector stored)")
    else:
        print("❌ Error saving snapshot.")

def handle_ask(args):
    print(f"🔍 Searching for: '{args.query}'")
    
    # 1. Vectorize the Query
    try:
        query_vec = model.encode(args.query).tolist()
    except Exception as e:
        print(f"❌ Error encoding query: {e}")
        return

    # 2. Search ChromaDB
    results = query_vectors(query_vec, n_results=3)
    
    if not results:
        print("📭 No relevant snapshots found.")
        return

    # 3. Display Results
    print(f"\n✅ Found {len(results)} relevant snapshots:\n")
    for snap_id, distance, doc_snippet in results:
        details = get_snapshot_details(snap_id)
        if details:
            timestamp, message, prompt, response = details
            score = 1 - distance # Approximate similarity
            print(f"------------------------------------------------")
            print(f"📸 ID: {snap_id[:8]} (Match: {score:.2f})")
            print(f"📅 Time: {timestamp}")
            print(f"💬 Message: {message}")
            print(f"❓ Context: {prompt[:100]}...") 
            print(f"------------------------------------------------")

def main():
    parser = argparse.ArgumentParser(description="VGIT CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=handle_init)

    snap_parser = subparsers.add_parser("snapshot")
    snap_parser.add_argument("-m", "--message", required=True)
    snap_parser.add_argument("-p", "--prompt", default="")
    snap_parser.add_argument("-r", "--response", default="")
    snap_parser.set_defaults(func=handle_snapshot)

    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("query")
    ask_parser.set_defaults(func=handle_ask)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
