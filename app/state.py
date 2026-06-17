from typing import TypedDict

class StoryState(TypedDict, total=False):
    user_input: str
    keywords: list[str]
    context: str
    story: str
    feedback: str
    approved: bool
    revision_count: int
    memory_updated: bool
