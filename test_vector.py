import time
from sentence_transformers import SentenceTransformer
import chromadb

def test_system():
    print("✅ Libraries imported successfully!")

    # 1. Initialize the Embedding Model
    print("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
    start_time = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"   -> Model loaded in {time.time() - start_time:.2f} seconds")

    # 2. Generate a Test Vector
    test_text = "Fixing the login bug in auth.py"
    print(f"🔤 Encoding text: '{test_text}'")
    embedding = model.encode(test_text)

    # 3. Validation
    print(f"🔢 Vector generated!")
    print(f"   -> Dimensions: {len(embedding)} (Should be 384)")
    print(f"   -> First 5 values: {embedding[:5]}")

    # 4. Test ChromaDB (Vector Store)
    print("💾 Testing ChromaDB (Storage)...")
    client = chromadb.PersistentClient(path="./vgit_test_db")
    collection = client.get_or_create_collection(name="test_collection")

    collection.add(
        documents=[test_text],
        embeddings=[embedding.tolist()],
        metadatas=[{"source": "test_script"}],
        ids=["test_id_1"]
    )
    print("   -> Data saved to ChromaDB!")
    print("🎉 Day 1 Sprint Complete: Environment is ready.")

if __name__ == "__main__":
    test_system()
