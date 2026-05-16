import os
import pickle
import re
import string

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    return [t for t in text.split() if t]


class BM25Retriever:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.bm25: BM25Okapi | None = None
        self.documents: list[dict] = []

    def build_index(self, chunks: list[dict]):
        self.documents = chunks
        tokenized = [tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"documents": self.documents}, f)

    def load_index(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"BM25 index not found at {self.index_path}. Run ingestion first.")
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
        self.documents = data["documents"]
        tokenized = [tokenize(c["text"]) for c in self.documents]
        self.bm25 = BM25Okapi(tokenized)

    def is_loaded(self) -> bool:
        return self.bm25 is not None

    def query(self, query_text: str, top_k: int = 10) -> list[dict]:
        if self.bm25 is None:
            return []
        tokenized_query = tokenize(query_text)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            {**self.documents[i], "bm25_score": float(scores[i])}
            for i in top_indices
            if scores[i] > 0
        ]
