from functools import lru_cache

from config.settings import Settings
from config.table_rules import TableRules
from ingestion.embedder import OllamaEmbedder
from llm.ollama_client import OllamaClient
from retrieval.bm25_retriever import BM25Retriever
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.vector_store import VectorStore


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def _get_settings() -> Settings:
    return get_settings()


def get_embedder() -> OllamaEmbedder:
    s = _get_settings()
    return OllamaEmbedder(base_url=s.ollama_base_url, model=s.embed_model)


def get_vector_store() -> VectorStore:
    s = _get_settings()
    return VectorStore(persist_dir=s.chromadb_path)


def get_bm25_retriever() -> BM25Retriever:
    s = _get_settings()
    b = BM25Retriever(index_path=s.bm25_index_path)
    b.load_index()
    return b


def get_hybrid_retriever() -> HybridRetriever:
    s = _get_settings()
    return HybridRetriever(
        vector_store=get_vector_store(),
        bm25_retriever=get_bm25_retriever(),
        embedder=get_embedder(),
        top_k=s.top_k,
    )


def get_table_rules() -> TableRules:
    s = _get_settings()
    return TableRules(file_path=s.table_rules_path)


def get_llm() -> OllamaClient:
    s = _get_settings()
    return OllamaClient(base_url=s.ollama_base_url, model=s.llm_model)
