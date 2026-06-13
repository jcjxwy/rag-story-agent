from typing import Callable
from langgraph.graph import START, END, StateGraph
from ..utils.logger import get_logger
from ..state import StoryState

logger = get_logger(__name__)

class StoryAgent:
    def __init__(
        self,
        parser,
        retriever,
        writer,
        feedback_collector,
        memory_updater,
        story_accept,
        max_revisions: int = 5,
    ):
        self.parser = parser
        self.retriever = retriever
        self.writer = writer
        self.feedback_collector = feedback_collector
        self.memory_updater = memory_updater
        self.max_revisions = max_revisions
        self.story_accept = story_accept
        self.graph = self._build_graph()

    def run(self, user_input: str) -> StoryState:
        return self.graph.invoke(
            {
                "user_input": user_input,
                "feedback": "",
                "approved": False,
                "revision_count": 0,
            }
        )

    def _build_graph(self):
        graph = StateGraph(StoryState)

        graph.add_node("parser", self.parser)
        graph.add_node("retriever", self.retriever)
        graph.add_node("writer", self.writer)
        graph.add_node("feedback_provider", self.feedback_provider)
        graph.add_node("memory_updater", self.memory_updater)

        graph.add_edge(START, "parser")
        graph.add_edge("parser", "retriever")
        graph.add_edge("retriever", "writer")
        graph.add_edge("writer", "feedback_provider")
        graph.add_conditional_edges(
            "feedback_provider",
            self.story_accept,
            {
                "revise": "generate_story",
                "approve": "memory_updater",
            },
        )
        graph.add_edge("memory_updater", END)

        return graph.compile()
