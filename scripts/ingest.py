"""CLI entry point for schema ingestion.

Usage:
    python -m scripts.ingest
    python -m scripts.ingest --file path/to/schema.xlsx
    python -m scripts.ingest --incremental
"""

import argparse
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from ingestion.embedder import OllamaEmbedder
from ingestion.indexer import Indexer
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest schema Excel into RAG knowledge base")
    parser.add_argument("--file", type=str, default=None, help="Path to Excel file")
    parser.add_argument("--incremental", action="store_true", help="Incremental update")
    args = parser.parse_args()

    settings = Settings()
    excel_path = args.file or settings.excel_input_path

    print(f"Loading Excel: {excel_path}")
    print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"ChromaDB path: {settings.chromadb_path}")
    print(f"BM25 index path: {settings.bm25_index_path}")
    print()

    embedder = OllamaEmbedder(
        base_url=settings.ollama_base_url,
        model=settings.embed_model,
    )
    vector_store = VectorStore(persist_dir=settings.chromadb_path)
    bm25_retriever = BM25Retriever(index_path=settings.bm25_index_path)
    indexer = Indexer(embedder, vector_store, bm25_retriever)

    report = indexer.run(excel_path, incremental=args.incremental)

    print(" Ingestion complete!")
    print(f"   Tables:    {report.num_tables}")
    print(f"   Chunks:    {report.num_chunks}")
    print(f"     - table: {report.table_chunks}")
    print(f"     - field: {report.field_chunks}")
    print(f"     - rel:   {report.relationship_chunks}")


if __name__ == "__main__":
    main()
