from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_bm25_retriever, get_embedder, get_settings, get_vector_store
from api.schemas.requests import ReindexRequest
from api.schemas.responses import ReindexResponse
from config.settings import Settings
from ingestion.embedder import OllamaEmbedder
from ingestion.indexer import Indexer
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_store import VectorStore

router = APIRouter(prefix="/api/reindex", tags=["reindex"])


@router.post("", response_model=ReindexResponse)
async def reindex(
    request: ReindexRequest,
    settings: Settings = Depends(get_settings),
    embedder: OllamaEmbedder = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
    bm25: BM25Retriever = Depends(get_bm25_retriever),
):
    excel_path = request.excel_path or settings.excel_input_path

    try:
        indexer = Indexer(embedder, vector_store, bm25)
        report = indexer.run(excel_path, incremental=request.incremental)

        return ReindexResponse(
            success=True,
            report={
                "num_tables": report.num_tables,
                "num_chunks": report.num_chunks,
                "table_chunks": report.table_chunks,
                "field_chunks": report.field_chunks,
                "relationship_chunks": report.relationship_chunks,
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
