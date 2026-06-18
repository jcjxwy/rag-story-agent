from state import StoryState
from langchain_core.runnables import RunnableConfig


class FeedbackCollector:
    def collect(self, state: StoryState) -> tuple[bool, bool, str]:
        """Returns (approved, abandoned, feedback)."""
        _display_story(state)
        answer = input("Action? [a]pprove / [r]evise / [q]uit: ").strip().lower()
        if answer in {"a", "approve"}:
            return True, False, ""
        if answer in {"q", "quit", "abandon"}:
            return False, True, ""
        feedback = input("What should be changed? ").strip()
        return False, False, feedback


def feedback_collector_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    feedback_provider = configurable.get("feedback_provider")

    if feedback_provider:
        if hasattr(feedback_provider, "collect"):
            result = feedback_provider.collect(state)
            if len(result) == 3:
                approved, abandoned, feedback = result
            else:
                approved, feedback = result
                abandoned = False
        else:
            approved, feedback = feedback_provider(state.get("story", ""))
            abandoned = False
        return {
            "approved": approved,
            "abandoned": abandoned,
            "feedback": "" if (approved or abandoned) else feedback.strip(),
        }

    _display_story(state)
    answer = input("Action? [a]pprove / [r]evise / [q]uit: ").strip().lower()
    if answer in {"a", "approve"}:
        return {"approved": True, "abandoned": False, "feedback": ""}
    if answer in {"q", "quit", "abandon"}:
        return {"approved": False, "abandoned": True, "feedback": ""}
    feedback = input("What should be changed? ").strip()
    return {"approved": False, "abandoned": False, "feedback": feedback}


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
