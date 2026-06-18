from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from state import StoryState
from langchain_core.runnables import RunnableConfig


class WorldSettingOutput(BaseModel):
    title: str = Field(description="A short name for this world setting document (10 words or fewer)")
    world_setting: str = Field(
        description=(
            "Structured world-building notes. Use headings and bullet points. "
            "Cover relevant elements such as geography, history, factions, culture, "
            "magic or technology systems, and key figures. No narrative or story."
        )
    )


class WorldBuilder:
    _SYSTEM_PROMPT = (
        "You are a world-building assistant for a fictional setting design tool.\n\n"
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
        self._structured_llm = llm.with_structured_output(WorldSettingOutput, method="function_calling")

    def build_world(self, prompt: str) -> WorldSettingOutput:
        return self._structured_llm.invoke([
            SystemMessage(content=self._SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])


def world_builder_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    world_builder = configurable.get("world_builder")
    prompt = _build_world_prompt(state)

    world_setting = ""
    title = ""

    if world_builder and hasattr(world_builder, "build_world"):
        result = world_builder.build_world(prompt)
        if isinstance(result, WorldSettingOutput):
            world_setting = result.world_setting
            title = result.title
        else:
            world_setting = str(result)
    else:
        world_setting = prompt

    if not title and world_setting:
        title = " ".join(world_setting.split()[:6])

    return {
        "story": world_setting,
        "story_title": title,
        "revision_count": state.get("revision_count", 0) + 1,
    }


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
