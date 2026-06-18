import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")))

import uuid
import streamlit as st
from langgraph.checkpoint.memory import MemorySaver

from graph import build_graph
from agent.generation.clients import LLMClient, EmbeddingClient
from agent.generation.writer import Writer
from agent.generation.world_builder import WorldBuilder
from agent.parser.input_parser import InputParser
from agent.retrieval.retriever import Retriever
from agent.memory.vault import Vault
from agent.memory.memory_updater import MemoryUpdater


st.set_page_config(page_title="Story Writer", layout="centered")
st.title("Story Writer")


# ── Session initialisation ────────────────────────────────────────────────────

def _init():
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph(checkpointer=MemorySaver())

    if "components" not in st.session_state:
        llm = LLMClient().llm
        embedder = EmbeddingClient()
        vault = Vault("data/vault")
        st.session_state.components = {
            "parser": InputParser(llm),
            "retriever": Retriever(vault, embedder, dim=EmbeddingClient.DIM),
            "writer": Writer(llm),
            "world_builder": WorldBuilder(llm),
            "memory_updater": MemoryUpdater(vault),
        }

    if "messages" not in st.session_state:
        st.session_state.messages = []   # committed chat history

    if "stage" not in st.session_state:
        st.session_state.stage = "idle"  # idle | reviewing | revising

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None


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


# ── Chat history ──────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Reviewing stage ───────────────────────────────────────────────────────────

if st.session_state.stage == "reviewing":
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
        with st.spinner("Revising story..."):
            _invoke()
        st.session_state.stage = "reviewing"
        st.rerun()

    if cancelled:
        _abandon(state.get("story_title", ""))


# ── Idle stage: prompt input ──────────────────────────────────────────────────

if st.session_state.stage == "idle":
    prompt = st.chat_input("Enter your story prompt…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.thread_id = str(uuid.uuid4())
        with st.spinner("Generating story…"):
            _invoke({"user_input": prompt})
        st.session_state.stage = "reviewing"
        st.rerun()
