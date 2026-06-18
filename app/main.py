import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from graph import build_graph
from agent.generation.clients import LLMClient, EmbeddingClient
from agent.generation.writer import Writer
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

    result = graph.invoke({"user_input": user_input}, config=config)

    print(f"\nStory saved to vault: {result.get('story_title', '')}")


if __name__ == "__main__":
    main()
