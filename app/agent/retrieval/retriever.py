from .vector_store import VectorStore
from ..memory.vault import Vault
from state import StoryState
from langchain_core.runnables import RunnableConfig


class Retriever:
    def __init__(self, vault: Vault, embedder, dim: int = 512, k: int = 5):
        self.vault = vault
        self.embedder = embedder
        self.dim = dim
        self.k = k
        self._stories: list[dict] = []
        self.vector_store = VectorStore(dim)
        self._build_indexes()

    def retrieve(
        self,
        query: str,
        keywords: list[str] | None = None,
        search_folders: list[str] | None = None,
    ) -> str:
        if not self._stories:
            return ""

        # Stage 1: semantic search
        # Cast a wider net when folder filtering is requested so filtering
        # doesn't leave us with too few candidates after narrowing the pool.
        candidate_k = len(self._stories) if search_folders else self.k * 2
        candidates = self._semantic_search(query, k=candidate_k)

        if search_folders:
            candidates = self._filter_by_folders(candidates, search_folders)

        # Stage 2: rerank surviving candidates by keyword field overlap
        ranked = self._rerank_by_keywords(candidates, keywords or [])
        top = ranked[:self.k]

        # Stage 3: expand with linked stories from the vault
        linked = self._graph_expand(top)

        return _format_context(top, linked, self._stories)

    def refresh(self):
        self.vector_store = VectorStore(self.dim)
        self._stories = []
        self._build_indexes()

    def _build_indexes(self):
        self._stories = self.vault.load_all()
        if not self._stories:
            return
        texts = [s["story"] for s in self._stories]
        embeddings = self.embedder.embed_documents(texts)
        self.vector_store.add(embeddings, list(range(len(texts))))

    def _semantic_search(self, query: str, k: int) -> list[int]:
        embedding = self.embedder.embed_query(query)
        return self.vector_store.search(embedding, k=k)

    def _filter_by_folders(self, indices: list[int], folders: list[str]) -> list[int]:
        folder_set = {f.lower() for f in folders}
        return [i for i in indices if self._stories[i].get("subdir", "").lower() in folder_set]

    def _rerank_by_keywords(self, indices: list[int], keywords: list[str]) -> list[int]:
        query_kws = {kw.lower() for kw in keywords}

        def overlap(idx: int) -> int:
            stored = {kw.lower() for kw in self._stories[idx]["frontmatter"].get("keywords", [])}
            return len(query_kws & stored)

        return sorted(indices, key=overlap, reverse=True)

    def _graph_expand(self, indices: list[int]) -> list[int]:
        title_to_idx = {
            s["frontmatter"].get("title"): i
            for i, s in enumerate(self._stories)
        }
        seen = set(indices)
        linked = []
        for idx in indices:
            title = self._stories[idx]["frontmatter"].get("title", "")
            for linked_title in self.vault.get_linked_stories(title):
                linked_idx = title_to_idx.get(linked_title)
                if linked_idx is not None and linked_idx not in seen:
                    seen.add(linked_idx)
                    linked.append(linked_idx)
        return linked


def _format_context(top: list[int], linked: list[int], stories: list[dict]) -> str:
    def render(idx: int, label: str) -> str:
        fm = stories[idx]["frontmatter"]
        title = fm.get("title", "untitled")
        keywords = ", ".join(fm.get("keywords", []))
        subdir = stories[idx].get("subdir", "")
        location = f" | folder: {subdir}" if subdir else ""
        return f"[{label}] {title}{location} | keywords: {keywords}\n\n{stories[idx]['story']}"

    parts = [render(i, "match") for i in top]
    parts += [render(i, "related") for i in linked]
    return "\n\n---\n\n".join(parts)


def retriever_node(state: StoryState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    retriever_instance = configurable.get("retriever")

    if not retriever_instance:
        return {"context": ""}

    if hasattr(retriever_instance, "retrieve"):
        context = retriever_instance.retrieve(
            state.get("user_input", ""),
            state.get("keywords"),
            state.get("search_folders"),
        )
    else:
        context = retriever_instance(state.get("user_input", ""))

    if isinstance(context, list):
        context = "\n\n".join(str(item) for item in context)

    return {"context": str(context)}
