from fastapi import APIRouter, Depends
import httpx

from api.dependencies import get_bm25_retriever, get_settings, get_vector_store
from api.schemas.responses import HealthResponse
from config.settings import Settings
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_store import VectorStore

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health(
    settings: Settings = Depends(get_settings),
    vector_store: VectorStore = Depends(get_vector_store),
    bm25: BM25Retriever = Depends(get_bm25_retriever),
):
    # Check Ollama
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    # Check ChromaDB
    chromadb_ok = False
    num_chunks = 0
    try:
        num_chunks = vector_store.count()
        chromadb_ok = True
    except Exception:
        chromadb_ok = False

    bm25_ok = bm25.is_loaded()

    all_ok = ollama_ok and chromadb_ok and bm25_ok

    return HealthResponse(
        status="ok" if all_ok else "degraded",
        ollama=ollama_ok,
        chromadb=chromadb_ok,
        bm25_index_loaded=bm25_ok,
        num_chunks=num_chunks,
    )
