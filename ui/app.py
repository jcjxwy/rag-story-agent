import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")))

import re
import uuid
import streamlit as st
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessageChunk

from graph import build_graph
from agent.generation.clients import LLMClient, EmbeddingClient
from agent.generation.writer import Writer
from agent.generation.world_builder import WorldBuilder
from agent.parser.input_parser import InputParser
from agent.retrieval.retriever import Retriever
from agent.memory.vault import Vault, slugify
from agent.memory.memory_updater import MemoryUpdater


st.set_page_config(page_title="Story Writer", layout="centered")
st.title("Story Writer")


# ── Session initialisation ────────────────────────────────────────────────────

def _init():
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph(checkpointer=MemorySaver())

    if "vault" not in st.session_state:
        st.session_state.vault = Vault("data/vault")

    if "components" not in st.session_state:
        llm = LLMClient().llm
        embedder = EmbeddingClient()
        vault = st.session_state.vault
        st.session_state.components = {
            "parser": InputParser(llm),
            "retriever": Retriever(vault, embedder, dim=EmbeddingClient.DIM),
            "writer": Writer(llm),
            "world_builder": WorldBuilder(llm),
            "memory_updater": MemoryUpdater(vault),
        }

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "stage" not in st.session_state:
        st.session_state.stage = "idle"  # idle | generating | reviewing | revising

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    if "generating_input" not in st.session_state:
        st.session_state.generating_input = None  # dict for new run, None to resume

    if "selected_world" not in st.session_state:
        st.session_state.selected_world = None  # {slug, title} or None


_init()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _thread_config():
    return {
        "configurable": {
            "thread_id": st.session_state.thread_id,
            **st.session_state.components,
        }
    }


def _current_state() -> dict:
    snapshot = st.session_state.graph.get_state(_thread_config())
    return snapshot.values if snapshot else {}


def _invoke(initial_state=None):
    st.session_state.graph.invoke(initial_state, config=_thread_config())


def _invoke_streaming(initial_state=None):
    """Stream writer/world_builder output word-by-word into a live placeholder."""
    placeholder = st.empty()
    buffer = ""

    for chunk, metadata in st.session_state.graph.stream(
        initial_state,
        config=_thread_config(),
        stream_mode="messages",
    ):
        if not isinstance(chunk, AIMessageChunk):
            continue
        if metadata.get("langgraph_node") not in ("writer", "world_builder"):
            continue
        if not isinstance(chunk.content, str) or not chunk.content:
            continue
        buffer += chunk.content
        placeholder.markdown(_stream_display(buffer) + "▌")

    # Show the final content without the cursor; rerun will replace this element.
    placeholder.markdown(_stream_display(buffer))


def _stream_display(buffer: str) -> str:
    """Strip the leading <title>…</title> tag while it streams in."""
    m = re.search(r"</title>\s*", buffer, re.DOTALL)
    if m:
        return buffer[m.end():]
    if buffer.lstrip().startswith("<title>"):
        return ""
    return buffer


def _inject_feedback(approved: bool, feedback: str = "", abandoned: bool = False):
    st.session_state.graph.update_state(
        _thread_config(),
        {"approved": approved, "abandoned": abandoned, "feedback": feedback},
        as_node="feedback_provider",
    )


def _abandon(label: str = ""):
    _inject_feedback(approved=False, abandoned=True)
    _invoke()
    note = f"Abandoned **{label}**. Nothing was saved." if label else "Abandoned. Nothing was saved."
    st.session_state.messages.append({"role": "assistant", "content": note})
    st.session_state.stage = "idle"
    st.rerun()


def _render_story(state: dict):
    title = state.get("story_title", "")
    revision = state.get("revision_count", 1)
    story = state.get("story", "")
    if title:
        st.markdown(f"### {title}")
        st.caption(f"Revision {revision}")
    st.markdown(story)
    return title, story


# ── Sidebar: World Settings ───────────────────────────────────────────────────

with st.sidebar:
    st.header("World Settings")
    worlds = st.session_state.vault.list_worlds()
    selected = st.session_state.selected_world

    if not worlds:
        st.caption("No worlds saved yet.")

    for world in worlds:
        is_active = selected is not None and selected["slug"] == world["slug"]
        header = f"✓ {world['title']}" if is_active else world["title"]

        with st.expander(header, expanded=is_active):
            st.markdown(world["intro"])
            st.divider()

            if is_active:
                if st.button("Deselect", key=f"sel_{world['slug']}", use_container_width=True):
                    st.session_state.selected_world = None
                    st.rerun()
            else:
                if st.button("Select", key=f"sel_{world['slug']}", use_container_width=True, type="primary"):
                    st.session_state.selected_world = {"slug": world["slug"], "title": world["title"]}
                    st.rerun()

            with st.form(f"rename_{world['slug']}"):
                new_name = st.text_input("Rename world", value=world["title"], label_visibility="collapsed")
                if st.form_submit_button("Rename", use_container_width=True):
                    new_name = str(new_name).strip()
                    if new_name and new_name != world["title"]:
                        ok = st.session_state.vault.rename_world(world["title"], new_name)
                        if ok:
                            if is_active:
                                st.session_state.selected_world = {"slug": slugify(new_name), "title": new_name}
                            st.rerun()
                        else:
                            st.error("Rename failed — a world with that name may already exist.")


# ── Chat history ──────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Generating stage ──────────────────────────────────────────────────────────
# Entered from both idle (new prompt) and revising (feedback submitted).
# Renders nothing above the stream so the user sees only fresh content.

if st.session_state.stage == "generating":
    with st.chat_message("assistant"):
        _invoke_streaming(st.session_state.generating_input)
    st.session_state.generating_input = None
    st.session_state.stage = "reviewing"
    st.rerun()


# ── Reviewing stage ───────────────────────────────────────────────────────────

elif st.session_state.stage == "reviewing":
    state = _current_state()

    with st.chat_message("assistant"):
        title, story = _render_story(state)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✓  Approve", use_container_width=True, type="primary"):
            _inject_feedback(approved=True)
            with st.spinner("Saving to vault..."):
                _invoke()
            story_md = f"### {title}\n\n{story}" if title else story
            st.session_state.messages.append({"role": "assistant", "content": story_md})
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Saved **{title}** to vault."}
            )
            st.session_state.stage = "idle"
            st.rerun()
    with col2:
        if st.button("↻  Revise", use_container_width=True):
            st.session_state.stage = "revising"
            st.rerun()
    with col3:
        if st.button("✕  Abandon", use_container_width=True):
            _abandon(title)


# ── Revising stage ────────────────────────────────────────────────────────────

elif st.session_state.stage == "revising":
    state = _current_state()

    with st.chat_message("assistant"):
        title, story = _render_story(state)

    with st.form("feedback_form", clear_on_submit=True):
        feedback = st.text_area("What should be changed?", placeholder="Be specific...")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Submit feedback", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("✕  Abandon", use_container_width=True)

    if submitted and feedback.strip():
        st.session_state.messages.append(
            {"role": "user", "content": f"Feedback: {feedback.strip()}"}
        )
        _inject_feedback(approved=False, feedback=feedback.strip())
        st.session_state.generating_input = None  # resume graph, no new initial state
        st.session_state.stage = "generating"
        st.rerun()

    if cancelled:
        _abandon(state.get("story_title", ""))


# ── Idle stage: prompt input ──────────────────────────────────────────────────

if st.session_state.stage == "idle":
    selected = st.session_state.selected_world
    if selected:
        st.info(f"Modifying world: **{selected['title']}**")

    placeholder_text = (
        f"How would you like to modify {selected['title']}?"
        if selected else "Enter your story or world-building prompt…"
    )
    prompt = st.chat_input(placeholder_text)
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.thread_id = str(uuid.uuid4())

        if selected:
            world_data = st.session_state.vault.load(selected["title"])
            existing_story = world_data["story"] if world_data else ""
            st.session_state.generating_input = {
                "user_input": f"Modify the world setting '{selected['title']}': {prompt}",
                "story": existing_story,
                "story_title": selected["title"],
                "world_name": selected["slug"],
            }
        else:
            st.session_state.generating_input = {"user_input": prompt}

        st.session_state.stage = "generating"
        st.rerun()
