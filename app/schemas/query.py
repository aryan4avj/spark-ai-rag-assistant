from typing import List, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    top_k: int = 4


class RetrievedChunkResponse(BaseModel):
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
