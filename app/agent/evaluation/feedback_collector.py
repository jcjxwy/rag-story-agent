from state import StoryState
from langchain_core.runnables import RunnableConfig


def feedback_collector_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    feedback_provider = configurable.get("feedback_provider")

    if feedback_provider:
        approved, feedback = feedback_provider(state.get("story", ""))
        return {
            "approved": approved,
            "feedback": "" if approved else feedback.strip(),
        }

    print("\nGenerated story:\n")
    print(state.get("story", ""))

    answer = input("\nApprove this story? [y/N]: ").strip().lower()
    if answer in {"y", "yes"}:
        return {
            "approved": True,
            "feedback": "",
        }

    feedback = input("What should be changed? ").strip()
    return {
        "approved": False,
        "feedback": feedback,
    }

def story_accept(state: StoryState):
    if state['approved']:
        return "approve"
    return 
    
