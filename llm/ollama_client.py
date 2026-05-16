import httpx


class OllamaClient:
    """Async client for Ollama /api/generate endpoint."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "deepseek-r1:8b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model or self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]
