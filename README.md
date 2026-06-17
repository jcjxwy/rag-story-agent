# AI Story Writer (RAG + LangGraph)

## Overview

A memory-augmented AI storytelling agent that generates stories using RAG (Retrieval-Augmented Generation). The agent retrieves semantically similar past stories as context, generates a new story, collects user feedback, and loops until approved.

---

## Architecture

```
User Input
↓
parser      — extracts keywords from the user prompt
↓
retriever   — semantic vector search over past stories (FAISS)
↓
writer      — builds prompt from input + context + feedback, calls LLM
↓
feedback_provider  — user approves or provides revision feedback
↓ (if rejected, loop back to writer)
memory_updater     — saves approved story to memory
↓
END
```

The graph is defined in [app/graph.py](app/graph.py) using LangGraph's `StateGraph`. Shared state across nodes is typed in [app/state.py](app/state.py) as `StoryState`.

---

## Project Structure

```text
story_writer/
├── app/
│   ├── agent/
│   │   ├── evaluation/
│   │   │   └── feedback_collector.py   # CLI prompt or injected feedback provider
│   │   ├── generation/
│   │   │   ├── llm_client.py           # DeepSeek LLM via OpenAI-compatible API
│   │   │   └── writer.py               # Prompt builder + writer node
│   │   ├── memory/
│   │   │   └── memory_updater.py       # Memory write-back node
│   │   ├── parser/
│   │   │   └── input_parser.py         # Keyword extraction from user input
│   │   └── retrieval/
│   │       ├── retriever.py            # Retriever node (FAISS-backed)
│   │       └── vector_store.py         # FAISS index wrapper
│   ├── utils/
│   │   └── logger.py
│   ├── graph.py                        # LangGraph graph definition
│   └── state.py                        # StoryState TypedDict
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## State

`StoryState` fields passed between nodes:

| Field            | Type        | Description                              |
|------------------|-------------|------------------------------------------|
| `user_input`     | `str`       | Raw user prompt                          |
| `keywords`       | `list[str]` | Extracted keywords from parser           |
| `context`        | `str`       | Retrieved memory context                 |
| `story`          | `str`       | Current generated story                  |
| `feedback`       | `str`       | User revision feedback                   |
| `approved`       | `bool`      | Whether the story was approved           |
| `revision_count` | `int`       | Number of generation attempts            |
| `memory_updated` | `bool`      | Whether memory was written back          |

---

## Nodes

**`parser`** — Uses an LLM agent with structured output to extract keywords (world setting, characters, writing style) from the user prompt.

**`retriever`** — Queries the FAISS vector store with the user input and returns relevant past stories as context. Falls back to a stub if no retriever is injected.

**`writer`** — Builds a prompt from `user_input`, `keywords`, `context`, and any `feedback` + previous `story`, then calls the LLM. Increments `revision_count` on each run.

**`feedback_provider`** — If a `feedback_provider` is injected via `config["configurable"]`, delegates to it. Otherwise falls back to interactive CLI (`input()`).

**`memory_updater`** — Calls the injected `memory_updater` (via `config["configurable"]`) to persist the approved story. No-ops if none is provided.

---

## Tech Stack

- **Python 3.10**
- **LangGraph** — graph orchestration and conditional feedback loop
- **LangChain** — LLM abstractions and agent tooling
- **DeepSeek** (`deepseek-chat`) — LLM via OpenAI-compatible API
- **FAISS** — vector similarity search
- **python-dotenv** — environment variable management

---

## Configuration

Copy `.env` and set your DeepSeek API key:

```
DEEPSEEK_API_KEY=your_key_here
```

---

## Installation

```bash
git clone https://github.com/jcjxwy/rag-story-agent.git
cd rag-story-agent
pip install -r requirements.txt
```

---

## Run

Components are injected via `config["configurable"]` when invoking the graph:

```python
from app.graph import build_graph
from app.agent.generation.llm_client import LLMClient

graph = build_graph().compile()
graph.invoke(
    {"user_input": "Write a sci-fi story about isolation in deep space"},
    config={
        "configurable": {
            "writer": LLMClient(),
            # "retriever": ...,
            # "memory_updater": ...,
            # "feedback_provider": ...,
        }
    }
)
```

If no `feedback_provider` is injected, the agent falls back to interactive CLI prompts.

---

## Docker

```bash
docker build -t story-writer .
docker run -e DEEPSEEK_API_KEY=your_key_here story-writer
```

---

## License

MIT License
