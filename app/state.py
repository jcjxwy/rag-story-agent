from typing import TypedDict

class StoryState(TypedDict, total=False):
    user_input: str
    keywords: list[str]
    search_folders: list[str]
    context: str
    story: str
    story_title: str
    feedback: str
    approved: bool
    revision_count: int
    memory_updated: bool
