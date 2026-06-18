from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from state import StoryState
from langchain_core.runnables import RunnableConfig


class ResponseFormat(BaseModel):
    keywords: list[str] = Field(
        description="Important story components: world setting, characters, themes, writing style"
    )
    search_folders: list[str] = Field(
        default_factory=list,
        description=(
            "Folder names to restrict the search to, if the user explicitly mentions a genre "
            "or category (e.g. 'from sci-fi', 'only fantasy'). "
            "Return lowercase hyphenated strings (e.g. ['sci-fi']). "
            "Empty list if no folder constraint is mentioned."
        ),
    )


_SYSTEM_PROMPT = (
    "You are the input processor for a story generator with a categorized memory vault.\n\n"
    "Extract two things from the user input:\n"
    "1. keywords: important story components (world setting, characters, themes, writing style) "
    "as a list of lowercase strings.\n"
    "2. search_folders: folder names only if the user explicitly restricts the search to a "
    "genre or category. Return lowercase hyphenated strings. Empty list if not mentioned."
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
        keywords = result.keywords
        search_folders = result.search_folders
    elif isinstance(result, dict):
        keywords = result.get("keywords", [])
        search_folders = result.get("search_folders", [])
    else:
        keywords = result if isinstance(result, list) else []
        search_folders = []

    if isinstance(keywords, str):
        keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    return {"keywords": keywords, "search_folders": search_folders}
