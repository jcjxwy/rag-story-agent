from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from state import StoryState
from langchain_core.runnables import RunnableConfig


class ResponseFormat(BaseModel):
    intent: Literal["story", "world_building"] = Field(
        description=(
            "'story' if the user wants a complete narrative or fiction piece. "
            "'world_building' if the user wants to brainstorm, design, or refine a setting, "
            "lore, world rules, factions, or background elements without a story."
        )
    )
    keywords: list[str] = Field(
        description="Important components: world setting, characters, themes, writing style"
    )
    world_name: str = Field(
        default="",
        description=(
            "If the user explicitly names an existing world or setting they want to write in "
            "or expand (e.g. 'in my Elden Vale world', 'add to the Cyberpunk 2087 setting'), "
            "return that name as a lowercase hyphenated slug (e.g. 'elden-vale', 'cyberpunk-2087'). "
            "Empty string when creating a brand-new world or when no specific world is referenced."
        ),
    )
    search_folders: list[str] = Field(
        default_factory=list,
        description=(
            "Folder names to restrict the vault search to. Include world_name here too if set. "
            "Return lowercase hyphenated strings. Empty list if not mentioned."
        ),
    )


_SYSTEM_PROMPT = (
    "You are the input processor for a creative writing assistant with a categorized memory vault.\n\n"
    "Classify the user's intent and extract structured information:\n\n"
    "1. intent: 'story' if they want a finished narrative; 'world_building' if they want to "
    "brainstorm or design a setting, lore, factions, magic system, history, or world rules "
    "— without a story.\n"
    "2. world_name: if the user explicitly references an existing named world or setting, "
    "return its name as a lowercase hyphenated slug (e.g. 'elden-vale'). "
    "Empty string when building a new world or when no specific world is named.\n"
    "3. keywords: important components (world setting, characters, themes, writing style) "
    "as lowercase strings.\n"
    "4. search_folders: folder names to restrict vault search. If world_name is set, include it. "
    "Lowercase hyphenated strings. Empty list if not applicable."
)


class InputParser:
    def __init__(self, llm):
        self._structured_llm = llm.with_structured_output(ResponseFormat, method="function_calling")

    def parse_input(self, user_input: str) -> ResponseFormat:
        return self._structured_llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ])


def parser_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    parser = configurable.get("parser")

    user_input = state.get("user_input", "")

    if parser:
        if hasattr(parser, "parse_input"):
            result = parser.parse_input(user_input)
        else:
            result = parser(user_input)
    else:
        return {"keywords": [], "search_folders": []}

    if isinstance(result, ResponseFormat):
        intent = result.intent
        world_name = result.world_name
        keywords = result.keywords
        search_folders = result.search_folders
    elif isinstance(result, dict):
        intent = result.get("intent", "story")
        world_name = result.get("world_name", "")
        keywords = result.get("keywords", [])
        search_folders = result.get("search_folders", [])
    else:
        intent = "story"
        world_name = ""
        keywords = result if isinstance(result, list) else []
        search_folders = []

    if isinstance(keywords, str):
        keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    return {"intent": intent, "world_name": world_name, "keywords": keywords, "search_folders": search_folders}
