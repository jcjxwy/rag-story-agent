from langgraph.graph import START, END, StateGraph
from .utils.logger import get_logger
from .state import StoryState

from agent.parser.input_parser import parser_node
from agent.retrieval.retriever import retriever_node
from agent.generation.writer import writer_node
from agent.evaluation.feedback_collector import feedback_collector_node
from agent.memory.memory_updater import memory_updater_node
from agent.evaluation.feedback_collector import story_accept

logger = get_logger(__name__)

def build_graph():
    graph = StateGraph(StoryState)

    graph.add_node("parser", parser_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("writer", writer_node)
    graph.add_node("feedback_provider", feedback_collector_node)
    graph.add_node("memory_updater", memory_updater_node)

    graph.add_edge(START, "parser")
    graph.add_edge("parser", "retriever")
    graph.add_edge("retriever", "writer")
    graph.add_edge("writer", "feedback_provider")
    graph.add_conditional_edges(
        "feedback_provider",
        story_accept,
        {
            "revise": "writer",
            "approve": "memory_updater",
        },
    )
    graph.add_edge("memory_updater", END)

    return graph.compile()
