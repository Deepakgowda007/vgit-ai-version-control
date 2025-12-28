import argparse
import sys
import uuid
import vgit_database as db

print("⏳ vGit: Loading AI Memory Layer...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

def handle_init(args):
    db.initialize_db()

def handle_snapshot(args):
    snapshot_id = str(uuid.uuid4())
    print(f"📸 Snapshotting Intent: {args.message} [{args.type}]")
    
    full_text = f"Intent: {args.prompt}\nOutcome: {args.response}"
    vector = model.encode(full_text).tolist()

    if db.add_snapshot(snapshot_id, args.message, args.prompt, args.response, args.type, 1 if args.stable else 0):
        db.save_vector(snapshot_id, full_text, vector)
        status = " (STABLE)" if args.stable else ""
        print(f"🎉 Captured Iteration {snapshot_id[:8]}{status}")

def handle_ask(args):
    print(f"🔍 Recalling context for: '{args.query}'")
    query_vec = model.encode(args.query).tolist()
    results = db.query_vectors(query_vec)
    
    if not results:
        print("📭 No matching memory found.")
        return

    print(f"\n✅ Relevant Memories Found:\n")
    for snap_id, distance, doc in results:
        details = db.get_snapshot_details(snap_id)
        if details:
            time, msg, _, _, task, stable = details
            score = 1 - distance
            
            # --- SAFETY GUARD FOR NULL VALUES ---
            display_task = (task or "legacy").upper()
            marker = "⭐ [STABLE]" if stable else ""
            
            print(f"[{score:.2f}] {snap_id[:8]} | {time} | {display_task:<8} | {msg} {marker}")

def handle_log(args):
    print("📜 vGit Knowledge Log:\n")
    snaps = db.get_all_snapshots()
    if not snaps:
        print("📭 Log is empty.")
        return

    for sid, time, msg, task, stable in snaps:
        # --- SAFETY GUARD FOR NULL VALUES ---
        display_task = (task or "legacy").upper()
        marker = "⭐ STABLE" if stable else "DRAFT"
        print(f"{sid[:8]} | {time} | {display_task:<8} | {marker:<8} | {msg}")

def handle_explain(args):
    details = db.get_snapshot_details(args.id)
    if not details:
        print("❌ Snapshot not found.")
        return
    
    time, msg, prompt, resp, task, stable = details
    display_task = (task or "legacy").upper()
    
    print(f"\n{'='*20} vGIT EXPLAIN {'='*20}")
    print(f"Snapshot: {args.id[:8]} ({'STABLE' if stable else 'DRAFT'})")
    print(f"Goal:     {msg}")
    print(f"Type:     {display_task}")
    print(f"Time:     {time}")
    print(f"\n[USER PROMPT]\n{prompt}")
    print(f"\n[AGENT RESPONSE]\n{resp[:300]}...")
    
    print(f"\n{'='*15} RELATED MEMORIES {'='*15}")
    vec = model.encode(prompt).tolist()
    related = db.query_vectors(vec, n_results=3)
    for rid, dist, _ in related:
        if rid[:8] != args.id[:8]:
            print(f" -> {rid[:8]} (Similarity: {1-dist:.2f})")
    print("="*53)

def handle_diff(args):
    files1 = set(db.get_manifest_content(args.id1) or [])
    files2 = set(db.get_manifest_content(args.id2) or [])
    
    if not files1 and not files2:
        print("❌ Could not retrieve manifests. Ensure IDs are correct.")
        return

    print(f"\n📂 Structural Diff: {args.id1[:8]} -> {args.id2[:8]}")
    added = files2 - files1
    removed = files1 - files2
    
    if added:
        print("\n➕ Files Added:")
        for f in added: print(f"  {f}")
    if removed:
        print("\n➖ Files Removed:")
        for f in removed: print(f"  {f}")
    if not added and not removed:
        print("\n✨ No structural changes (File content may have changed).")

def handle_status(args):
    s = db.get_status()
    if not s:
        print("No snapshots yet.")
        return
    print(f"📊 Status: {s['total']} tracked files.")
    if s['new']:
        print("New (Untracked):")
        for f in s['new']: print(f" + {f}")
    if s['deleted']:
        print("Deleted:")
        for f in s['deleted']: print(f" - {f}")
    if not s['new'] and not s['deleted']:
        print("✨ Working directory clean.")

def handle_resume(args):
    details = db.get_snapshot_details(args.id)
    files = db.get_manifest_content(args.id)
    if not details or not files:
        print("❌ Invalid snapshot ID.")
        return
    print(f"\n🔄 RESUMING {args.id[:8]}\n\nFiles in this state:")
    for f in files: print(f"  - {f}")
    print(f"\nCONTEXT:\nPrompt: {details[2]}\nResponse: {details[3]}")

def main():
    parser = argparse.ArgumentParser(description="vGit: Agentic Memory Layer")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    
    snap = subparsers.add_parser("snapshot")
    snap.add_argument("-m", "--message", required=True)
    snap.add_argument("-p", "--prompt", required=True)
    snap.add_argument("-r", "--response", default="")
    snap.add_argument("--type", choices=['feat', 'bug', 'refactor'], default='feat')
    snap.add_argument("--stable", action="store_true")
    snap.set_defaults(func=handle_snapshot)

    subparsers.add_parser("log").set_defaults(func=handle_log)
    subparsers.add_parser("status").set_defaults(func=handle_status)
    
    ask = subparsers.add_parser("ask").add_argument("query")
    subparsers.choices['ask'].set_defaults(func=handle_ask)

    exp = subparsers.add_parser("explain").add_argument("id")
    subparsers.choices['explain'].set_defaults(func=handle_explain)

    df = subparsers.add_parser("diff")
    df.add_argument("id1")
    df.add_argument("id2")
    df.set_defaults(func=handle_diff)

    res = subparsers.add_parser("resume").add_argument("id")
    subparsers.choices['resume'].set_defaults(func=handle_resume)

    args = parser.parse_args()
    if args.command:
        if args.command == "init": handle_init(args)
        elif hasattr(args, 'func'): args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
