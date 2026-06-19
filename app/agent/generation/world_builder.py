import re
from langchain_core.messages import SystemMessage, HumanMessage
from state import StoryState
from langchain_core.runnables import RunnableConfig


class WorldBuilder:
    _SYSTEM_PROMPT = (
        "You are a world-building assistant for a fictional setting design tool.\n\n"
        "Format your response exactly like this:\n"
        "<title>A short name for this world setting (10 words or fewer)</title>\n\n"
        "Then write the world-building notes.\n\n"
        "Rules:\n"
        "- DO NOT write any story, narrative, plot, or character arcs\n"
        "- Focus ONLY on world elements: geography, history, culture, factions, "
        "magic systems, technology, languages, religions, economies, key figures\n"
        "- Present information as structured notes with clear headings and bullet points\n"
        "- When existing world settings are provided, extend or refine them — "
        "do not discard established facts unless the user explicitly requests a change\n"
        "- Be internally consistent and creatively detailed"
    )

    def __init__(self, llm):
        self._llm = llm

    def stream_world(self, prompt: str):
        return self._llm.stream([
            SystemMessage(content=self._SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])


def world_builder_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    world_builder = configurable.get("world_builder")
    prompt = _build_world_prompt(state)

    full_content = ""
    if world_builder and hasattr(world_builder, "stream_world"):
        for chunk in world_builder.stream_world(prompt):
            if hasattr(chunk, "content") and chunk.content:
                full_content += chunk.content
    elif world_builder:
        full_content = str(world_builder(prompt))
    else:
        full_content = prompt

    title, world_setting = _parse_output(full_content)
    if not title and world_setting:
        title = " ".join(world_setting.split()[:6])

    return {
        "story": world_setting,
        "story_title": title,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def _parse_output(content: str) -> tuple[str, str]:
    m = re.match(r"<title>(.*?)</title>\s*", content, re.DOTALL)
    if m:
        return m.group(1).strip(), content[m.end():].strip()
    return "", content.strip()


def _build_world_prompt(state: StoryState) -> str:
    is_revision = bool(state.get("feedback"))

    sections = [
        "Modify the existing world setting based on the feedback below. "
        "Preserve all established facts unless the feedback explicitly changes them."
        if is_revision else
        "Design a world setting based on the user's request.",
        f"User request:\n{state.get('user_input', '')}",
    ]

    if state.get("keywords"):
        sections.append(f"Key elements to include:\n{', '.join(state.get('keywords', []))}")

    if not is_revision and state.get("context"):
        sections.append(f"Existing world settings for reference:\n{state.get('context', '')}")

    if is_revision:
        sections.append(
            f"Feedback:\n{state.get('feedback', '')}\n\n"
            f"Current world setting:\n{state.get('story', '')}"
        )

    return "\n\n".join(sections)
