from fastapi import APIRouter, Depends

from api.dependencies import get_vector_store
from api.schemas.responses import SchemaResponse
from retrieval.vector_store import VectorStore

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.get("", response_model=SchemaResponse)
async def list_tables(vector_store: VectorStore = Depends(get_vector_store)):
    # Get all unique tables from the collection
    try:
        results = vector_store.collection.get(include=["metadatas"])
        table_map: dict[str, dict] = {}

        for meta in results.get("metadatas", []):
            if not meta:
                continue
            chunk_type = meta.get("chunk_type", "")
            table_name = meta.get("table", "")
            if not table_name:
                continue

            if table_name not in table_map:
                table_map[table_name] = {
                    "name": table_name,
                    "subs_code": meta.get("subs_code", ""),
                    "num_fields": 0,
                }

            if chunk_type == "field":
                table_map[table_name]["num_fields"] += 1

        return SchemaResponse(tables=list(table_map.values()))
    except Exception:
        return SchemaResponse(tables=[])
