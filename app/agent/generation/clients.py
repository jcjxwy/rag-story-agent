from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import SecretStr
from dotenv import load_dotenv
import os

load_dotenv()

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


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
    DIM = 384  # all-MiniLM-L6-v2 output dimension

    def __init__(self):
        self.embedder = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", _EMBEDDING_MODEL),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embedder.embed_query(text)
