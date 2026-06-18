from typing import TypedDict

class StoryState(TypedDict, total=False):
    intent: str          # "story" | "world_building"
    world_name: str      # slug of the world directory (e.g. "elden-vale")
    user_input: str
    keywords: list[str]
    search_folders: list[str]
    context: str
    story: str
    story_title: str
    feedback: str
    approved: bool
    abandoned: bool
    revision_count: int
    memory_updated: bool
