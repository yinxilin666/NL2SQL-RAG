from typing import Optional

from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    sql: str
    reasoning: Optional[str] = None
    retrieved_tables: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    execution_time_ms: float


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    chromadb: bool
    bm25_index_loaded: bool
    num_chunks: int


class SchemaResponse(BaseModel):
    tables: list[dict] = Field(default_factory=list)


class ReindexResponse(BaseModel):
    success: bool
    report: dict = Field(default_factory=dict)
