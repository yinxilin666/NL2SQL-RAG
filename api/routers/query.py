import time

from fastapi import APIRouter, Depends

from api.dependencies import get_hybrid_retriever, get_llm
from api.schemas.requests import QueryRequest
from api.schemas.responses import QueryResponse
from llm.ollama_client import OllamaClient
from llm.prompt_templates import build_prompt
from llm.response_parser import parse_llm_response
from llm.sql_validator import validate_hive_sql
from retrieval.hybrid_retriever import HybridRetriever

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    llm: OllamaClient = Depends(get_llm),
):
    t_start = time.perf_counter()

    chunks = retriever.retrieve(request.question)

    prompt = build_prompt(
        user_query=request.question,
        retrieved_chunks=chunks,
        few_shot=request.few_shot,
    )

    raw_output = await llm.generate(
        prompt=prompt,
        temperature=request.temperature,
    )

    parsed = parse_llm_response(raw_output)

    validation = validate_hive_sql(parsed["sql"])

    retrieved_tables = list(set(
        c.get("metadata", {}).get("table", "")
        for c in chunks
        if c.get("metadata", {}).get("table")
    ))

    elapsed = (time.perf_counter() - t_start) * 1000

    return QueryResponse(
        sql=parsed["sql"] or "-- No valid SQL generated",
        reasoning=parsed["reasoning"] if request.include_reasoning else None,
        retrieved_tables=retrieved_tables,
        warnings=validation.warnings,
        execution_time_ms=round(elapsed, 2),
    )
