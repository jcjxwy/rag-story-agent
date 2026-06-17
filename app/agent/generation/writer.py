from state import StoryState
from langchain_core.runnables import RunnableConfig


def writer_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    writer = configurable.get("writer")
    prompt = _build_prompt(state)

    if writer:
        if hasattr(writer, "generate_story"):
            story = writer.generate_story(prompt)
        elif hasattr(writer, "write"):
            story = writer.write(prompt)
        else:
            story = writer(prompt)
    else:
        story = prompt

    return {
        "story": story,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def _build_prompt(state: StoryState):
    prompt_sections = [
        "Write a story based on the user request.",
        f"User request:\n{state.get('user_input', '')}",
    ]

    if state.get("keywords"):
        prompt_sections.append(f"Important keywords:\n{', '.join(state['keywords'])}")

    if state.get("context"):
        prompt_sections.append(f"Relevant memory context:\n{state['context']}")

    if state.get("feedback"):
        prompt_sections.append(
            "Revise the previous story using this user feedback:\n"
            f"{state['feedback']}\n\n"
            f"Previous story:\n{state.get('story', '')}"
        )

    return "\n\n".join(prompt_sections)
