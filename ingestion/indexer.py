import os
from dataclasses import dataclass

from config.constants import CHUNK_TYPE_TABLE
from ingestion.chunker import chunk_all
from ingestion.embedder import OllamaEmbedder
from ingestion.loader import load_excel
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_store import VectorStore


@dataclass
class IndexReport:
    num_tables: int
    num_chunks: int
    table_chunks: int
    field_chunks: int
    relationship_chunks: int


class Indexer:
    def __init__(
        self,
        embedder: OllamaEmbedder,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever

    def run(self, excel_path: str, incremental: bool = False) -> IndexReport:
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        result = load_excel(excel_path)
        all_chunks = chunk_all(result.tables)

        table_chunks = sum(
            1 for c in all_chunks if c["metadata"]["chunk_type"] == CHUNK_TYPE_TABLE
        )
        field_chunks = sum(
            1 for c in all_chunks if c["metadata"]["chunk_type"] == "field"
        )
        rel_chunks = sum(
            1 for c in all_chunks if c["metadata"]["chunk_type"] == "relationship"
        )

        texts = [c["text"] for c in all_chunks]
        embeddings = self.embedder.embed(texts)

        if incremental and self.vector_store.count() > 0:
            self.vector_store.upsert(
                ids=[c["id"] for c in all_chunks],
                embeddings=embeddings,
                metadatas=[c["metadata"] for c in all_chunks],
                documents=texts,
            )
        else:
            self.vector_store.add(
                ids=[c["id"] for c in all_chunks],
                embeddings=embeddings,
                metadatas=[c["metadata"] for c in all_chunks],
                documents=texts,
            )

        self.bm25_retriever.build_index(all_chunks)

        return IndexReport(
            num_tables=len(result.tables),
            num_chunks=len(all_chunks),
            table_chunks=table_chunks,
            field_chunks=field_chunks,
            relationship_chunks=rel_chunks,
        )
