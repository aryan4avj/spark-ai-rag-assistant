from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = 4


class RetrievedChunkResponse(BaseModel):
    source_number: int
    chunk_id: str
    doc_id: str
    title: str
    section: Optional[str] = None
    space: str
    content: str
    url: Optional[str] = None


class RetrieveResponse(BaseModel):
    question: str
    chunks: List[RetrievedChunkResponse]


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[RetrievedChunkResponse]


class AgentQueryResponse(BaseModel):
    question: str
    route: str
    answer: str
    sources: List[RetrievedChunkResponse]
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
    timing_ms: Dict[str, float] = Field(default_factory=dict)
