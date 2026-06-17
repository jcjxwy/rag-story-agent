from .vector_store import VectorStore
from state import StoryState
from langchain_core.runnables import RunnableConfig

class retriever:
    def __init__(self, dim=512):
        self.vector_store = VectorStore(dim)

    def retrieve(self, query):
        # Implement retrieval logic here
        return "Retrieved results for query: " + query


def retriever_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    retriever_instance = configurable.get("retriever")

    if retriever_instance:
        if hasattr(retriever_instance, "retrieve"):
            context = retriever_instance.retrieve(state.get("user_input", ""))
        else:
            context = retriever_instance(state.get("user_input", ""))
    else:
        context = retriever().retrieve(state.get("user_input", ""))

    if isinstance(context, list):
        context = "\n\n".join(str(item) for item in context)

    return {"context": str(context)}
