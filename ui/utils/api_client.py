import httpx

BACKEND_URL = "http://localhost:8000"


async def query_nl2sql(question: str, top_k: int, temperature: float,
                        include_reasoning: bool, few_shot: bool) -> dict:
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/query",
            json={
                "question": question,
                "top_k": top_k,
                "temperature": temperature,
                "include_reasoning": include_reasoning,
                "few_shot": few_shot,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def health_check() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BACKEND_URL}/api/health")
        resp.raise_for_status()
        return resp.json()


async def get_schema() -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BACKEND_URL}/api/schema")
        resp.raise_for_status()
        return resp.json().get("tables", [])


async def get_rules() -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BACKEND_URL}/api/rules")
        resp.raise_for_status()
        return resp.json().get("rules", [])


async def reindex(excel_path: str | None = None, incremental: bool = True) -> dict:
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/reindex",
            json={
                "excel_path": excel_path,
                "incremental": incremental,
            },
        )
        resp.raise_for_status()
        return resp.json()
