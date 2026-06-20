import sys
import os
from typing import cast

sys.path.insert(0, os.path.dirname(__file__))

from langchain_core.runnables import RunnableConfig
from graph import build_graph
from state import StoryState
from agent.generation.clients import LLMClient, EmbeddingClient
from agent.generation.writer import Writer
from agent.generation.world_builder import WorldBuilder
from agent.parser.input_parser import InputParser
from agent.retrieval.retriever import Retriever
from agent.memory.vault import Vault
from agent.memory.memory_updater import MemoryUpdater
from agent.evaluation.feedback_collector import FeedbackCollector


def main():
    llm = LLMClient().llm
    embedder = EmbeddingClient()
    vault = Vault("data/vault")

    graph = build_graph()

    config = {
        "configurable": {
            "parser": InputParser(llm),
            "retriever": Retriever(vault, embedder, dim=EmbeddingClient.DIM),
            "writer": Writer(llm),
            "world_builder": WorldBuilder(llm),
            "feedback_provider": FeedbackCollector(),
            "memory_updater": MemoryUpdater(vault),
        }
    }

    print("Story Writer")
    print("=" * 60)
    user_input = input("Enter your story prompt: ").strip()
    if not user_input:
        print("No input provided.")
        return

    result = graph.invoke(StoryState(user_input=user_input), config=cast(RunnableConfig, config))

    print(f"\nStory saved to vault: {result.get('story_title', '')}")


if __name__ == "__main__":
    main()
