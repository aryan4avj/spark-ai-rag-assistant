from pydantic import BaseModel


class ReindexResponse(BaseModel):
    status: str
    documents_indexed: int
    chunks_indexed: int
    vector_size: int
