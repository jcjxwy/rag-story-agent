from state import StoryState
from langchain_core.runnables import RunnableConfig


class FeedbackCollector:
    def collect(self, state: StoryState) -> tuple[bool, str]:
        _display_story(state)
        answer = input("Approve this story? [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True, ""
        feedback = input("What should be changed? ").strip()
        return False, feedback


def feedback_collector_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    feedback_provider = configurable.get("feedback_provider")

    if feedback_provider:
        if hasattr(feedback_provider, "collect"):
            approved, feedback = feedback_provider.collect(state)
        else:
            approved, feedback = feedback_provider(state.get("story", ""))
        return {
            "approved": approved,
            "feedback": "" if approved else feedback.strip(),
        }

    _display_story(state)
    answer = input("Approve this story? [y/N]: ").strip().lower()
    if answer in {"y", "yes"}:
        return {"approved": True, "feedback": ""}

    feedback = input("What should be changed? ").strip()
    return {"approved": False, "feedback": feedback}


def story_accept(state: StoryState) -> str:
    return "approve" if state.get("approved") else "revise"


def _display_story(state: StoryState):
    title = state.get("story_title", "")
    revision = state.get("revision_count", 1)
    divider = "=" * 60
    print(f"\n{divider}")
    if title:
        print(f"Title:    {title}")
    print(f"Revision: {revision}")
    print(divider)
    print(state.get("story", ""))
    print(divider)
