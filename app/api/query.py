from fastapi import APIRouter

from app.retrieval.rag_pipeline import RAGPipeline
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    RetrieveResponse,
    RetrievedChunkResponse,
)

router = APIRouter(prefix="", tags=["rag"])

pipeline = RAGPipeline()


def to_chunk_response(chunk, source_number: int) -> RetrievedChunkResponse:
    return RetrievedChunkResponse(
        source_number=source_number,
        chunk_id=chunk.metadata.chunk_id,
        doc_id=chunk.metadata.doc_id,
        title=chunk.metadata.title,
        section=chunk.metadata.section,
        space=chunk.metadata.space,
        content=chunk.content,
        url=chunk.metadata.url,
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: QueryRequest) -> RetrieveResponse:
    chunks = pipeline.retrieve(question=request.question, limit=request.top_k)

    return RetrieveResponse(
        question=request.question,
        chunks=[
            to_chunk_response(chunk, source_number=i)
            for i, chunk in enumerate(chunks, start=1)
        ],
    )


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    answer, chunks = pipeline.answer(question=request.question, limit=request.top_k)

    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=[
            to_chunk_response(chunk, source_number=i)
            for i, chunk in enumerate(chunks, start=1)
        ],
    )