# VGIT - Version Control for AI Context

VGIT is a Command Line Interface (CLI) tool designed to solve the "Context Window" problem in AI-assisted coding. unlike Git, which tracks code changes, VGIT tracks the **conversational context** and **reasoning** behind those changes.

## Features
- **📸 Snapshot:** Captures code state (`.diff`) and AI conversation history simultaneously.
- **🧠 Vector Embeddings:** Uses `sentence-transformers` to convert prompts into semantic vectors.
- **🔍 Semantic Search:** Allows developers to search history using natural language (e.g., `vgit ask "how to fix auth"`).
- **🔒 Local-First:** All data is stored locally in `.vgit/` using SQLite and ChromaDB.

## Tech Stack
- Python 3.x
- SQLite & ChromaDB
- Sentence-Transformers (all-MiniLM-L6-v2)
