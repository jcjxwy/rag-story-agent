from state import StoryState
from langchain_core.runnables import RunnableConfig


def memory_updater_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    memory_updater = configurable.get("memory_updater")

    if not memory_updater:
        return {"memory_updated": False}

    if hasattr(memory_updater, "update"):
        result = memory_updater.update(state)
    elif hasattr(memory_updater, "save"):
        result = memory_updater.save(state.get("story", ""), state)
    else:
        result = memory_updater(state)

    if isinstance(result, dict):
        return result

    return {"memory_updated": bool(result)}
