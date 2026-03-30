from datetime import date
from pydantic import BaseModel, Field
from typing import List, Optional


class DocumentMetadata(BaseModel):
    doc_id: str
    title: str
    source: str
    source_type: str = "local_markdown"
    space: str
    author: str
    created_at: date
    updated_at: date
    tags: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class Document(BaseModel):
    metadata: DocumentMetadata
    content: str


class ChunkMetadata(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    source: str
    source_type: str = "local_markdown"
    space: str
    section: Optional[str] = None
    chunk_index: int
    tags: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class Chunk(BaseModel):
    metadata: ChunkMetadata
    content: str
