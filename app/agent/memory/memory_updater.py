from state import StoryState
from langchain_core.runnables import RunnableConfig
from .vault import Vault


class MemoryUpdater:
    def __init__(self, vault: Vault):
        self.vault = vault

    def update(self, state: StoryState) -> dict:
        title = state.get("story_title", "")
        if not title:
            raise ValueError("StoryState is missing 'story_title'")
        self.vault.save(title, state.get("story", ""), state.get("keywords", []))
        return {"memory_updated": True}


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
