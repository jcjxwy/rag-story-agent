import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []

    def add(self, embeddings: list, texts: list):
        self.index.add(np.array(embeddings).astype("float32"))
        self.texts.extend(texts)

    def search(self, query_embedding: list, k: int = 5) -> list:
        k = min(k, len(self.texts))
        if k == 0:
            return []
        D, I = self.index.search(np.array([query_embedding]).astype("float32"), k)
        return [self.texts[i] for i in I[0] if i >= 0]
