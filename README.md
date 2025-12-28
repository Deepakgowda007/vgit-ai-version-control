# 🚀 vGit: Semantic Memory Layer for AI Agents (Context Control)

**vGit** is a specialized **context control system** designed not just for code, but for the **AI context behind the code**.

While traditional Git performs *version control* by tracking line-by-line code changes, **vGit performs context control** by tracking **user intent, AI responses, and semantic project snapshots**.  
This creates a persistent **Semantic Memory Layer** that helps:

- prevent AI hallucinations  
- preserve long-term reasoning context  
- enable non-coders to manage complex AI-driven iterations  

---

## 🌟 Key Features

### 🧠 Semantic Recall
Search your project history using natural language.

> Example:  
> *“Find the version where the login button was blue”*

---

### 📸 Context Snapshots
Capture the **exact reasoning context** at any point:
- User Prompt  
- AI Response  
- Project file structure  

---

### 🛡️ Anti-Hallucination Grounding
Resume past *working contexts* to re-ground the AI when it starts drifting or hallucinating.

---

### ⭐ Stable Checkpoints
Mark important iterations as **STABLE**, creating safe fallback contexts for **Agentic IDEs**.

---

### 🔍 Structural Auditing
Track which files were added or removed **without the complexity of binary diffs**.

---

## 🛠️ Installation

### 1. Prerequisites
- Python **3.9+**
- Virtual environment (recommended)

---

### 2. Clone and Setup

```bash
git clone https://github.com/Deepakgowda007/vgit-ai-version-control.git
cd vgit_project

python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

### 3. Global Command Installation

To use `vgit` from anywhere in your terminal:

```bash
pip install -e .
```

---

## 📋 Command Cheat Sheet

| Command | Usage | Best Used When |
|------|------|---------------|
| `vgit init` | `vgit init` | Starting a new project |
| `vgit snapshot` | `vgit snapshot -m "msg" -p "prompt"` | Capturing a completed AI iteration |
| `vgit log` | `vgit log` | Viewing the context timeline |
| `vgit ask` | `vgit ask "query"` | Recalling *when and why* something worked |
| `vgit explain` | `vgit explain <id>` | Inspecting full AI context |
| `vgit diff` | `vgit diff <id1> <id2>` | Comparing structural context changes |
| `vgit resume` | `vgit resume <id>` | Restoring a known-good AI context |
| `vgit status` | `vgit status` | Checking changes since last snapshot |

---

## 🚀 Detailed Usage Guide

### 1. Initialize vGit Context Control

```bash
vgit init
```

---

### 2. Capture a Context Snapshot

```bash
vgit snapshot -m "Added product gallery" \
              -p "Create a responsive 3-column grid for shoe products" \
              -r "Generated HTML/CSS for product_grid.html" \
              --type feat --stable
```

---

### 3. Semantic Context Search

```bash
vgit ask "product grid layout"
```

---

### 4. Explain a Snapshot (Context Explanation)

```bash
vgit explain <snapshot_id>
```

---

### 5. Restore Context (The Time Machine)

```bash
vgit resume <snapshot_id>
```

---

## 📂 Project Architecture

- **SQLite**  
  Stores structured metadata: timestamps, messages, task types, stability flags

- **ChromaDB**  
  Vector database for semantic recall of AI prompts and responses

- **Sentence-Transformers**  
  Model: `all-MiniLM-L6-v2` (384-dimensional embeddings)

- **File Manifests**  
  Lightweight snapshots of project structure (context-level)

---

## 🎭 The “Shoe Store” Scenario (MVP Use Case)

Imagine a **non-coder** building a shoe website using an Agentic IDE.

At **Iteration 91**, the AI hallucinates and breaks the shopping cart.

### Context-Controlled Recovery Flow

1. **Discovery**
   ```bash
   vgit ask "working shopping cart"
   ```

2. **Identification**  
   vGit finds **Iteration 81** with a high similarity score.

3. **Context Restoration**
   ```bash
   vgit resume <iteration_81_id>
   ```

4. **Resolution**  
   vGit restores:
   - original prompt
   - successful AI response
   - project structure  

   allowing the user or agent to **resume from a stable mental context** instead of starting over.

---

## 📜 License

MIT License  
Created by **Deepak Gowda**
