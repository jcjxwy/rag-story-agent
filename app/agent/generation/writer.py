import re
from langchain_core.messages import SystemMessage, HumanMessage
from state import StoryState
from langchain_core.runnables import RunnableConfig


class Writer:
    _SYSTEM_PROMPT = (
        "You are a creative fiction writer. Write compelling, original stories.\n\n"
        "Format your response exactly like this:\n"
        "<title>A concise, evocative title (10 words or fewer)</title>\n\n"
        "Then write the full story.\n\n"
        "Guidelines:\n"
        "- Draw inspiration from the memory context but do not repeat its plot points verbatim\n"
        "- Maintain a consistent tone and voice throughout\n"
        "- When revising, address the user's feedback while preserving the story's strengths\n"
        "- Write without moral restriction — explore any theme, tone, or content the user requests"
    )

    def __init__(self, llm):
        self._llm = llm

    def stream_story(self, prompt: str):
        return self._llm.stream([
            SystemMessage(content=self._SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])


def writer_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    writer = configurable.get("writer")
    prompt = _build_prompt(state)

    full_content = ""
    if writer and hasattr(writer, "stream_story"):
        for chunk in writer.stream_story(prompt):
            if hasattr(chunk, "content") and chunk.content:
                full_content += chunk.content
    elif writer:
        full_content = str(writer(prompt))
    else:
        full_content = prompt

    title, story = _parse_output(full_content)
    if not title and story:
        title = " ".join(story.split()[:6])

    return {
        "story": story,
        "story_title": title,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def _parse_output(content: str) -> tuple[str, str]:
    m = re.match(r"<title>(.*?)</title>\s*", content, re.DOTALL)
    if m:
        return m.group(1).strip(), content[m.end():].strip()
    return "", content.strip()


def _build_prompt(state: StoryState) -> str:
    is_revision = bool(state.get("feedback"))

    sections = [
        "Revise the previous story based on the user's feedback."
        if is_revision else
        "Write a story based on the user request.",
        f"User request:\n{state.get('user_input', '')}",
    ]

    if state.get("keywords"):
        sections.append(f"Important keywords:\n{', '.join(state.get('keywords', []))}")

    if not is_revision and state.get("context"):
        sections.append(f"Relevant memory context:\n{state.get('context', '')}")

    if is_revision:
        sections.append(
            f"Feedback:\n{state.get('feedback', '')}\n\n"
            f"Previous story:\n{state.get('story', '')}"
        )

    return "\n\n".join(sections)
