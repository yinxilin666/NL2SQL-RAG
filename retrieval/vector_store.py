import os
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.constants import COLLECTION_NAME


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = COLLECTION_NAME):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ):
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ):
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        where: Optional[dict] = None,
    ) -> list[dict]:
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        items = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for i in range(len(ids)):
            items.append({
                "id": ids[i],
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else 0.0,
            })
        return items

    def delete_by_ids(self, ids: list[str]):
        self.collection.delete(ids=ids)

    def count(self) -> int:
        return self.collection.count()
