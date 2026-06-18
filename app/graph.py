from langgraph.graph import START, END, StateGraph
from utils.logger import get_logger
from state import StoryState

from agent.parser.input_parser import parser_node
from agent.retrieval.retriever import retriever_node
from agent.generation.writer import writer_node
from agent.generation.world_builder import world_builder_node
from agent.evaluation.feedback_collector import feedback_collector_node
from agent.memory.memory_updater import memory_updater_node

logger = get_logger(__name__)


def _route_by_intent(state: StoryState) -> str:
    return "world_builder" if state.get("intent") == "world_building" else "writer"


def _route_after_feedback(state: StoryState) -> str:
    if state.get("approved"):
        return "approve"
    if state.get("abandoned"):
        return "abandon"
    return "revise_world" if state.get("intent") == "world_building" else "revise_story"


def build_graph(checkpointer=None):
    graph = StateGraph(StoryState)

    graph.add_node("parser", parser_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("writer", writer_node)
    graph.add_node("world_builder", world_builder_node)
    graph.add_node("feedback_provider", feedback_collector_node)
    graph.add_node("memory_updater", memory_updater_node)

    graph.add_edge(START, "parser")
    graph.add_edge("parser", "retriever")
    graph.add_conditional_edges(
        "retriever",
        _route_by_intent,
        {"writer": "writer", "world_builder": "world_builder"},
    )
    graph.add_edge("writer", "feedback_provider")
    graph.add_edge("world_builder", "feedback_provider")
    graph.add_conditional_edges(
        "feedback_provider",
        _route_after_feedback,
        {
            "revise_story": "writer",
            "revise_world": "world_builder",
            "approve": "memory_updater",
            "abandon": END,
        },
    )
    graph.add_edge("memory_updater", END)

    if checkpointer:
        return graph.compile(checkpointer=checkpointer, interrupt_before=["feedback_provider"])
    return graph.compile()
