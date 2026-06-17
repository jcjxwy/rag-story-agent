from langchain.agents import create_agent
from dataclasses import dataclass
from state import StoryState
from langchain_core.runnables import RunnableConfig

@dataclass
class ResponseFormat:
    keywords: list

class InputParser:
    def __init__(self, llm):
        self.llm = llm

    def parse_input(self, input):
        systemPrompt = \
        '''
        You are the user input processor of a story generator in charge of generating story based on user input.
        Your job is to extract the keywords from user input.
        The keywords should include important story components such as world setting, characters, writing style.
        The keywords should be returned as a list of string.
        '''
        agent = create_agent(
            model=self.llm,
            system_prompt=systemPrompt,
            response_format=ResponseFormat
        )
        response = agent.invoke(
            {'messages':[
                {'role': 'user', 'content': input}
            ]}
        )
        return response['structured_response'].keywords
    
def parser_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    parser = configurable.get("parser")

    user_input = state.get("user_input", "")

    if parser:
        if hasattr(parser, "parse_input"):
            keywords = parser.parse_input(user_input)
        else:
            keywords = parser(user_input)
    else:
        keywords = []

    if isinstance(keywords, str):
        keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    return {"keywords": keywords}