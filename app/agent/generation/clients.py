from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr
from dotenv import load_dotenv
import os

load_dotenv()

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class LLMClient:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=SecretStr(api_key),
            base_url=_DEEPSEEK_BASE_URL,
            temperature=0.7,
        )


class EmbeddingClient:
    DIM = 1536  # dimension for deepseek-embedding

    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        self.embedder = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "deepseek-embedding"),
            api_key=SecretStr(api_key),
            base_url=os.getenv("EMBEDDING_BASE_URL", _DEEPSEEK_BASE_URL),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embedder.embed_query(text)
