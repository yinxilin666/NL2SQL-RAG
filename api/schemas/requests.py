from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=8, ge=1, le=30)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    include_reasoning: bool = Field(default=False)
    few_shot: bool = Field(default=True)


class ReindexRequest(BaseModel):
    excel_path: str | None = Field(default=None)
    incremental: bool = Field(default=True)
