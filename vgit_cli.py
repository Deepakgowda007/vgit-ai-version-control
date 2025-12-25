import argparse
import sys
import uuid
# Import everything including the new get_status function
from vgit_database import initialize_db, add_snapshot, save_vector, query_vectors, get_snapshot_details, get_all_snapshots, get_status

print("⏳ Loading AI Model...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ AI Model Loaded.")
except Exception as e:
    print(f"❌ Error loading AI model: {e}")
    sys.exit(1)

def handle_init(args):
    """Initialize the VGIT repository."""
    print("Initializing VGIT...")
    initialize_db()

def handle_snapshot(args):
    """Capture a new snapshot of code + context."""
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
    """Search for past context."""
    print(f"🔍 Searching for: '{args.query}'")
    try:
        query_vec = model.encode(args.query).tolist()
    except Exception as e:
        print(f"❌ Error encoding query: {e}")
        return

    results = query_vectors(query_vec, n_results=3)
    
    if not results:
        print("📭 No relevant snapshots found.")
        return

    print(f"\n✅ Found {len(results)} relevant snapshots:\n")
    for snap_id, distance, doc_snippet in results:
        details = get_snapshot_details(snap_id)
        if details:
            timestamp, message, prompt, response = details
            score = 1 - distance
            print(f"------------------------------------------------")
            print(f"📸 ID: {snap_id[:8]} (Match: {score:.2f})")
            print(f"📅 Time: {timestamp}")
            print(f"💬 Message: {message}")
            print(f"❓ Context: {prompt[:100]}...") 
            print(f"------------------------------------------------")

def handle_log(args):
    """Show commit history."""
    print("📜 VGIT History:\n")
    snapshots = get_all_snapshots()
    
    if not snapshots:
        print("📭 No snapshots found in history.")
        return

    for snap_id, timestamp, message, prompt in snapshots:
        print(f"🔹 Commit: {snap_id[:8]}")
        print(f"   Date:   {timestamp}")
        print(f"   Msg:    {message}")
        print(f"   Prompt: {prompt[:60]}...")
        print("")

def handle_status(args):
    """Show current repository status."""
    print("📊 VGIT Status:\n")
    status = get_status()
    
    if status["status"] != "Active":
        print(f"Status: {status['status']}")
        return

    print(f"✅ Tracking {status['total_tracked']} files from last snapshot.")
    
    if status["new"]:
        print("\n🆕 New Files (Untracked):")
        for f in status["new"]:
            print(f"   + {f}")
            
    if status["deleted"]:
        print("\n❌ Deleted Files:")
        for f in status["deleted"]:
            print(f"   - {f}")
            
    if not status["new"] and not status["deleted"]:
        print("\n✨ Working directory clean (No new/deleted files).")

def main():
    parser = argparse.ArgumentParser(description="VGIT CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=handle_init)

    # snapshot
    snap_parser = subparsers.add_parser("snapshot")
    snap_parser.add_argument("-m", "--message", required=True)
    snap_parser.add_argument("-p", "--prompt", default="")
    snap_parser.add_argument("-r", "--response", default="")
    snap_parser.set_defaults(func=handle_snapshot)

    # ask
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("query")
    ask_parser.set_defaults(func=handle_ask)

    # log
    log_parser = subparsers.add_parser("log", help="Show history")
    log_parser.set_defaults(func=handle_log)

    # status (NEW)
    status_parser = subparsers.add_parser("status", help="Show working tree status")
    status_parser.set_defaults(func=handle_status)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
