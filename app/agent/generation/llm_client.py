from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=0.7,
        )


class EmbeddingClient:
    DIM = 1536  # dimension for text-embedding-3-small

    def __init__(self):
        kwargs = {}
        base_url = os.getenv("EMBEDDING_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url

        self.embedder = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embedder.embed_query(text)
