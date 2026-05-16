from collections import defaultdict

from config.constants import RRF_K
from ingestion.embedder import OllamaEmbedder
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_store import VectorStore


class HybridRetriever:
    """Combines vector similarity search and BM25 keyword search via RRF fusion."""

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
        embedder: OllamaEmbedder,
        top_k: int = 8,
    ):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, query: str) -> list[dict]:
        query_emb = self.embedder.embed([query])[0]

        vector_results = self.vector_store.query(query_emb, top_k=self.top_k * 2)
        bm25_results = self.bm25_retriever.query(query, top_k=self.top_k * 2)

        rrf_scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, dict] = {}

        for rank, doc in enumerate(vector_results):
            rrf_scores[doc["id"]] += 1.0 / (RRF_K + rank + 1)
            doc_map[doc["id"]] = doc

        for rank, doc in enumerate(bm25_results):
            rrf_scores[doc["id"]] += 1.0 / (RRF_K + rank + 1)
            if doc["id"] not in doc_map:
                doc_map[doc["id"]] = doc

        ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

        final = []
        for doc_id in ranked_ids:
            doc = doc_map[doc_id]
            doc["rrf_score"] = rrf_scores[doc_id]
            final.append(doc)
            if len(final) >= self.top_k:
                break

        return final
