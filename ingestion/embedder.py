import httpx


class OllamaEmbedder:
    """Embed texts using a locally running Ollama model."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
