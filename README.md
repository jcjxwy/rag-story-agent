📖 AI Story Memory Agent (RAG + Obsidian Memory System)
🧠 Overview

This project is a memory-augmented AI storytelling agent that generates coherent and evolving narratives using a hybrid retrieval system.

It combines:

Retrieval-Augmented Generation (RAG)
Vector similarity search (FAISS or similar)
Graph-based memory (Obsidian-style markdown links)
Persistent local knowledge storage

The system allows the agent to remember and reuse its own previously generated stories, enabling long-term narrative consistency and world-building.

🚀 Key Features
📚 Memory-based storytelling using past generated stories
🔍 Hybrid retrieval system
Semantic search (vector embeddings)
Relationship search (markdown links / graph)
🧩 Obsidian-style knowledge vault
✍️ LLM-powered story generation
🔄 Self-updating memory system
💬 Optional Streamlit UI for interaction
🏗️ Architecture
User Input
   ↓
Story Agent (Orchestrator)
   ↓
Retriever
   ├── Vector Search (semantic similarity)
   └── Graph Search (linked notes)
   ↓
Context Builder
   ↓
LLM Generator
   ↓
Story Output
   ↓
Memory Store (Markdown Vault)
📁 Project Structure
rag-story-agent/
│
├── app/
│   ├── agent/              # Core agent logic
│   ├── memory/             # Vault + graph memory system
│   ├── retrieval/          # Vector + hybrid retrieval
│   ├── generation/         # LLM + prompt engineering
│   ├── pipelines/          # Ingestion + memory updates
│   ├── utils/              # Helper functions
│
├── ui/                     # Streamlit UI (optional)
│
├── data/
│   ├── vault/              # Markdown story memory (Obsidian-style)
│   ├── index/              # Vector index storage
│
├── tests/
├── requirements.txt
└── README.md
⚙️ How It Works
1. Memory Storage

All generated stories are stored as Markdown files in a local vault.

Each story may include:

Tags (#sci-fi, #fantasy)
Links ([[related story]])
2. Retrieval

When a user prompt is given:

Convert input into embeddings
Retrieve similar past stories
Expand using linked graph structure
3. Generation

The retrieved context is formatted into a prompt and passed to an LLM to generate a new story.

4. Memory Update

After generation:

The new story is saved into the vault
Links and metadata are updated
It becomes part of future retrieval
🧪 Example
Input:

“Write a sci-fi story about isolation in space”

Output:

A newly generated story influenced by:

previous “space isolation” stories
related themes like loneliness, survival, AI companionship
🧰 Tech Stack
Python
FAISS / vector database
OpenAI API (or any LLM provider)
Markdown-based memory system
Streamlit (optional UI)
📦 Setup
git clone https://github.com/yourname/rag-story-agent.git
cd rag-story-agent

pip install -r requirements.txt
▶️ Run
CLI version:
python app/main.py
UI version (if enabled):
streamlit run ui/app.py
🔮 Future Improvements
Add reranking model for better retrieval
Improve memory summarization (reduce redundancy)
Add multi-agent system (writer + critic)
Deploy as web app (FastAPI + React)
Add visualization for memory graph
📌 Design Philosophy

This project explores how AI systems can evolve through self-generated memory, combining:

structured storage (Markdown vault)
semantic retrieval (embeddings)
relational reasoning (graph links)
📄 License

MIT License