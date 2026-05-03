from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Wrapper of the LLM client and related operations
class LLMClient:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.7
        )

    def generate_story(self, input):
        return self.llm.invoke(input).content