# AI Handover — Story Writer Project

## Project Overview

A memory-augmented AI creative writing agent with two modes: **story writing** and **world building**. The user provides a prompt; the agent classifies the intent, retrieves relevant context from a local Markdown vault, generates content via DeepSeek LLM (streamed word-by-word), collects user feedback in a revision loop (with approve / revise / abandon options), and saves approved content back to the vault. Each world gets its own vault directory; stories written in that world are stored alongside its world-building document.

---

## How to Run

**CLI:**
```bash
python app/main.py
```

**UI (Streamlit):**
```bash
streamlit run ui/app.py
```

**Docker:**
```bash
docker build -t story-writer .
docker run -e DEEPSEEK_API_KEY=... story-writer
```

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | Yes | DeepSeek chat LLM **and** embeddings |
| `EMBEDDING_MODEL` | No | Override embedding model (default: `deepseek-embedding`) |
| `EMBEDDING_BASE_URL` | No | Override embedding endpoint (default: `https://api.deepseek.com`) |

> Only one API key is required. Both `LLMClient` and `EmbeddingClient` use `DEEPSEEK_API_KEY`.

---

## Architecture

```
User Input
    ↓
parser          Classifies intent (story | world_building)
                Extracts keywords, world_name, search_folders
    ↓
retriever       Stage 1: FAISS semantic search
                Stage 2: filter by search_folders (optional)
                Stage 3: rerank by vault keywords field overlap
                Stage 4: graph expand via [[wikilinks]] (1-hop)
    ↓
    ├── intent=story ──────── writer        → streams story via <title> tag format
    └── intent=world_building  world_builder → streams world notes (no narrative)
    ↓
feedback_provider   User approves, requests revision, or abandons
    ├── approve  → memory_updater → END
    ├── revise   → back to writer / world_builder
    └── abandon  → END (nothing saved)
    ↓
memory_updater  Saves to vault:
                  world_building → data/vault/<slugify(title)>/
                  story (with world_name) → data/vault/<world_name>/
                  story (no world_name) → data/vault/
```

The graph is defined in `app/graph.py` using LangGraph `StateGraph`. Shared state is `StoryState` (`app/state.py`).

---

## Project Structure

```
story_writer/
├── app/
│   ├── main.py                         CLI entry point
│   ├── graph.py                        LangGraph graph + routing functions
│   ├── state.py                        StoryState TypedDict
│   ├── utils/
│   │   └── logger.py
│   └── agent/
│       ├── generation/
│       │   ├── clients.py              LLMClient + EmbeddingClient (both DeepSeek)
│       │   ├── writer.py               Writer (streaming), writer_node, _build_prompt
│       │   └── world_builder.py        WorldBuilder (streaming), world_builder_node
│       ├── parser/
│       │   └── input_parser.py         InputParser, ResponseFormat, parser_node
│       ├── retrieval/
│       │   ├── retriever.py            Retriever (3-stage pipeline), retriever_node
│       │   └── vector_store.py         FAISS index wrapper
│       ├── memory/
│       │   ├── vault.py                Vault (Obsidian-style Markdown)
│       │   └── memory_updater.py       MemoryUpdater, memory_updater_node
│       └── evaluation/
│           └── feedback_collector.py   FeedbackCollector, feedback_collector_node
├── ui/
│   └── app.py                          Streamlit chatbot UI
├── data/
│   └── vault/                          Markdown files (created at runtime)
│       └── <world-name>/               One directory per world
│           ├── <world-name>.md         World building document
│           └── <story-title>.md        Stories set in this world
├── pyrightconfig.json                  extraPaths: ["app"]
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Key Design Decisions

### StoryState fields
```python
intent          # "story" | "world_building" — set by parser
world_name      # slug of the target world dir (e.g. "elden-vale") — set by parser
user_input      # raw user prompt
keywords        # extracted by parser
search_folders  # vault subdirs to restrict retrieval (set by parser)
context         # formatted retrieval results (set by retriever)
story           # current story or world-setting draft
story_title     # title parsed from LLM output (used as vault filename)
feedback        # revision feedback (empty when approved or abandoned)
approved        # bool — set by feedback_collector_node
abandoned       # bool — set by feedback_collector_node; routes to END without saving
revision_count  # incremented by writer_node / world_builder_node
memory_updated  # bool — set by memory_updater_node
```

### LLM output format (streaming)
Both `Writer` and `WorldBuilder` instruct the LLM to prefix output with a title tag:
```
<title>The Concise Title Here</title>

Full content follows...
```
The nodes collect the full stream, parse title/body with `_parse_output()`. In the UI,
`_stream_display()` hides the tag while it is accumulating and shows only the content.

### Vault file format
```markdown
---
title: Elden Vale World Notes
date: '2026-06-20'
keywords: [fantasy, magic, factions]
related: ['[[the-first-hero]]']
---

## Geography
...

## Related
- [[the-first-hero]]
```

World-building docs and their stories share one directory:
```
data/vault/
├── elden-vale/
│   ├── elden-vale-world-notes.md   ← world building doc
│   ├── the-first-hero.md           ← story in this world
│   └── siege-of-the-keep.md
└── standalone-story.md             ← story with no world
```

### Graph routing
After `retriever`, intent determines the generation node:
```python
def _route_by_intent(state) -> str:
    return "world_builder" if state.get("intent") == "world_building" else "writer"
```

After `feedback_provider`, three routes:
```python
def _route_after_feedback(state) -> str:
    if state.get("approved"):  return "approve"
    if state.get("abandoned"): return "abandon"   # → END, nothing saved
    return "revise_world" if state.get("intent") == "world_building" else "revise_story"
```

### Graph compilation modes
- **No checkpointer** (CLI): straight-through; `FeedbackCollector.collect()` uses CLI `input()`; returns `(approved, abandoned, feedback)` 3-tuple
- **With `MemorySaver`** (UI): `interrupt_before=["feedback_provider"]`; UI injects state via `graph.update_state(..., as_node="feedback_provider")`

### Streaming in the UI
`_invoke_streaming()` in `ui/app.py` calls `graph.stream(stream_mode="messages")`. Chunks from `writer` or `world_builder` nodes (filtered by `metadata["langgraph_node"]`) are written to a `st.empty()` placeholder. The `<title>` tag is hidden during accumulation via `_stream_display()`.

The UI has four stages: `idle → generating → reviewing → revising`
- `generating` stage was added to avoid double-rendering the old story above the streaming new content when feedback is submitted.

---

## Development Timeline

### Session 2026-06-18 — Initial Implementation
All core agent code was written from scratch:
- Vault, MemoryUpdater, InputParser, Retriever (3-stage), Writer, FeedbackCollector, graph wiring, CLI entry point, Streamlit UI, bug fixes across all files.
- See original handover for full detail of this session's work.

### Session 2026-06-20 — Features & Bug Fixes

#### Fixes
- **`EmbeddingClient` switched from OpenAI to DeepSeek** — was failing at startup with `OPENAI_API_KEY` not set. Now uses `DEEPSEEK_API_KEY` + `https://api.deepseek.com` with `deepseek-embedding` model. `EmbeddingClient.DIM` updated from 1536 to match DeepSeek's embedding output.
- **`LLMClient.api_key` now validated** — added `if not api_key: raise ValueError(...)` and wraps key in `SecretStr` to satisfy LangChain's type requirement.
- **`with_structured_output` → `method="function_calling"`** — DeepSeek rejects the default `json_schema` response format; function calling is supported. Applied to both `InputParser` and (at the time) `Writer`. Later both were rewritten to use plain streaming instead.
- **`_slugify` renamed to `slugify`** in `vault.py` — function is now used by `memory_updater.py` as a public import; underscore prefix was misleading.
- **Pylance type fixes** in `main.py`: input to `graph.invoke()` cast to `StoryState`; config cast to `RunnableConfig` via `typing.cast`.
- **Pylance type fix** in `ui/app.py` line 97: `chunk.content` typed as `str | list[...]`; replaced `chunk.content or ""` with `isinstance(chunk.content, str)` guard.

#### World Building Feature
- Added `intent: str` and `world_name: str` to `StoryState`
- `input_parser.py` — `ResponseFormat` extended with `intent: Literal["story", "world_building"]` and `world_name: str`; system prompt updated; `parser_node` returns both new fields
- Created `app/agent/generation/world_builder.py` — `WorldBuilder` class with `stream_world(prompt)`, `world_builder_node`, `_build_world_prompt`; system prompt explicitly forbids narrative writing
- `graph.py` — added `_route_by_intent` (after retriever) and `_route_after_feedback` (after feedback); added `world_builder` node; removed old `story_accept` import
- `memory_updater.py` — saves world-building docs to `data/vault/<slugify(title)>/`; saves stories to `data/vault/<world_name>/` if set, else vault root
- `main.py` + `ui/app.py` — `WorldBuilder(llm)` wired into `configurable`

#### World-based Vault Directory Structure
- `state.py` — added `world_name: str`
- `input_parser.py` — parser also extracts `world_name` (explicit world reference in user prompt → lowercase hyphenated slug); includes it in `search_folders` when set
- `memory_updater.py` — uses `slugify(title)` as subdir for world building; uses `world_name` as subdir for stories

#### Abandon Feature
- `state.py` — added `abandoned: bool`
- `feedback_collector.py` — `FeedbackCollector.collect()` returns 3-tuple `(approved, abandoned, feedback)`; CLI prompt changed to `[a]pprove / [r]evise / [q]uit`; removed `story_accept` (replaced by `_route_after_feedback` in graph)
- `graph.py` — `_route_after_feedback` handles `"abandon"` → `END`; `"approve"` → `memory_updater`; `"revise_story"` → `writer`; `"revise_world"` → `world_builder`
- `ui/app.py` — Abandon button added to reviewing stage (3-column layout); Abandon button inside the revising feedback form

#### Real-time Streaming
- `writer.py` — rewrote to use `llm.stream()` directly (removed Pydantic `StoryOutput` + `with_structured_output`); LLM instructed to prefix output with `<title>…</title>`; `Writer.stream_story(prompt)` returns the stream iterator; `writer_node` collects chunks, parses title/body via `_parse_output()`
- `world_builder.py` — same streaming rewrite; `WorldBuilder.stream_world(prompt)` returns stream
- `ui/app.py`:
  - Added `_invoke_streaming()` — iterates `graph.stream(stream_mode="messages")`, filters for writer/world_builder node chunks, updates `st.empty()` placeholder; shows final content without cursor on completion (no `placeholder.empty()` to avoid flash)
  - Added `_stream_display()` — hides `<title>` tag while it accumulates, shows content once `</title>` is seen
  - Added `"generating"` stage — entered from both idle (new prompt) and revising (feedback submitted); renders only the streaming content with nothing above it; transitions to reviewing on completion
  - Idle stage now sets `generating_input` + transitions to `"generating"` instead of streaming inline

---

## Known Issues / Work To Be Done

### Must fix before production use

1. **Retriever not refreshed after save** — `Retriever._build_indexes()` runs once at init. After `memory_updater` saves a new story, the FAISS index is stale; the next prompt will not find the newly saved content. Fix: call `retriever.refresh()` in `memory_updater_node` after saving, or expose a `refresh` hook on the graph.

2. **No `__init__.py` files** — `retriever.py` uses relative imports (`from .vector_store import VectorStore`, `from ..memory.vault import Vault`). Python 3 namespace packages handle this in most setups, but if import errors occur on a fresh install, add empty `__init__.py` to `app/agent/`, `app/agent/retrieval/`, `app/agent/memory/`, etc.

### Nice to have

- **Tests** — no tests exist. Priority: `vault.py` (save/load/backlinks/subdir), `_build_prompt` (fresh vs revision), `_build_world_prompt`, retriever pipeline stages, graph routing (`_route_by_intent`, `_route_after_feedback`).
- **`story_title` slug collisions** — `slugify(title)` may collide for similar titles. Consider appending a short timestamp in `memory_updater.py`.
- **World name mismatch on retrieval** — when a story references a world by name, `search_folders` is set but the actual world directory slug might not match exactly what the parser returns. If retrieval misses the world context, the LLM won't have it. A fuzzy folder match in `retriever.py` would help.
- **Retriever `dim` default** — `Retriever` has `dim=512` as default but `EmbeddingClient.DIM` is 1536 (or whatever DeepSeek returns). The default is misleading; consider removing it and requiring the caller to pass it explicitly.

---

## Component Instantiation Reference

```python
from langchain_core.runnables import RunnableConfig
from typing import cast
from graph import build_graph
from state import StoryState
from agent.generation.clients import LLMClient, EmbeddingClient
from agent.generation.writer import Writer
from agent.generation.world_builder import WorldBuilder
from agent.parser.input_parser import InputParser
from agent.retrieval.retriever import Retriever
from agent.memory.vault import Vault
from agent.memory.memory_updater import MemoryUpdater
from agent.evaluation.feedback_collector import FeedbackCollector  # CLI only

llm      = LLMClient().llm
embedder = EmbeddingClient()
vault    = Vault("data/vault")

config = {
    "configurable": {
        "parser":            InputParser(llm),
        "retriever":         Retriever(vault, embedder, dim=EmbeddingClient.DIM),
        "writer":            Writer(llm),
        "world_builder":     WorldBuilder(llm),
        "feedback_provider": FeedbackCollector(),   # omit in UI mode
        "memory_updater":    MemoryUpdater(vault),
    }
}

graph = build_graph()   # no checkpointer for CLI
# graph = build_graph(checkpointer=MemorySaver())  # for Streamlit UI

# CLI invocation
result = graph.invoke(StoryState(user_input="..."), config=cast(RunnableConfig, config))

# UI invocation (in ui/app.py, via graph.stream + graph.update_state)
```

### FeedbackCollector.collect() return signature
```python
# Returns (approved: bool, abandoned: bool, feedback: str)
# approved=True  → save to vault
# abandoned=True → discard, go to END
# both False     → revise (feedback contains the user's request)
```
