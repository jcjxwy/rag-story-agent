# 📖 AI Story Memory Agent (RAG + Obsidian Memory System)

## 🧠 Overview

This project is a memory-augmented AI storytelling agent that generates coherent and evolving narratives using a hybrid retrieval system.

It combines:
- Retrieval-Augmented Generation (RAG)
- Vector similarity search (FAISS or similar)
- Graph-based memory (Obsidian-style Markdown links)
- Persistent local knowledge storage

The system allows the agent to remember and reuse its own previously generated stories, enabling long-term narrative consistency and world-building.

---

## 🚀 Key Features

- Memory-based storytelling using previously generated stories
- Hybrid retrieval system:
  - Semantic search (vector embeddings)
  - Relationship search (markdown links / graph structure)
- Obsidian-style knowledge vault (Markdown files)
- LLM-powered story generation
- Self-updating memory loop (write-back to vault)
- Optional Streamlit UI for interaction and debugging

---

## 🏗️ Architecture

User Input  
↓  
Story Agent (Orchestrator)  
↓  
Retriever  
- Vector Search (semantic similarity)  
- Graph Search (Obsidian links)  
↓  
Context Builder  
↓  
LLM Generator  
↓  
Story Output  
↓  
Memory Store (Markdown Vault)  
↓  
Index + Graph Update  

---

## 📁 Project Structure

```text
rag-story-agent/
├── app/
│   ├── agent/
│   │   └── story_agent.py
│   ├── memory/
│   │   ├── vault.py
│   │   ├── parser.py
│   │   └── graph.py
│   ├── retrieval/
│   │   ├── embedder.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── generation/
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   └── writer.py
│   ├── pipelines/
│   │   ├── ingest.py
│   │   └── update.py
│   └── utils/
│
├── ui/
│   └── app.py
│
├── data/
│   ├── vault/
│   └── index/
│
├── tests/
├── requirements.txt
└── README.md
```

---

## ⚙️ How It Works

### 1. Memory Storage
All generated stories are stored as Markdown files in a local vault.

Each story may include:
- Tags (#sci-fi, #fantasy)
- Links ([[related story]])
- Metadata (theme, tone, characters)

---

### 2. Retrieval (RAG + Graph)
When a user prompt is received:
- Convert query into embeddings
- Retrieve semantically similar stories
- Expand context using linked notes

---

### 3. Context Building
Retrieved memory is transformed into structured context:
- themes
- narrative patterns
- related story elements

---

### 4. Story Generation
A language model generates a new story using:
- user prompt
- retrieved memory context
- constraints (no repetition, maintain coherence)

---

### 5. Memory Update Loop
After generation:
- Save story to vault
- Update graph links
- Refresh vector index

---

## 🧪 Example

Input:
Write a sci-fi story about isolation in deep space

Output:
A new story influenced by:
- previous space isolation stories
- themes like loneliness and survival
- related narrative structures from memory

---

## 🧰 Tech Stack

- Python
- FAISS (vector search)
- OpenAI API (or compatible LLM)
- Markdown-based memory system
- Streamlit (optional UI)

---

## 📦 Installation

git clone https://github.com/jcjxwy/rag-story-agent.git  
cd rag-story-agent  

pip install -r requirements.txt  

---

## ▶️ Run

CLI mode:
python app/main.py  

UI mode (optional):
streamlit run ui/app.py  

---

## 🔮 Future Improvements

- Add reranking model for retrieval
- Improve memory summarization
- Add multi-agent system (writer + critic)
- Deploy with FastAPI backend
- Add graph visualization (Obsidian-like UI)
- Support multi-user story worlds

---

## 📌 Design Philosophy

This system explores how AI agents can evolve through persistent self-generated memory, combining:

- Structured storage (Markdown vault)
- Semantic retrieval (embeddings)
- Relational reasoning (graph links)

The goal is to simulate long-term narrative intelligence where stories influence future generations of stories.

---

## 📄 License

MIT License