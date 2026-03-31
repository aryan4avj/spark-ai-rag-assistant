from dataclasses import dataclass

from app.core.providers import get_embedding_client
from app.ingestion.chunk import chunk_documents
from app.ingestion.local_files import load_markdown_documents
from app.vectorstore.qdrant_store import QdrantVectorStore


@dataclass
class ReindexResult:
    document_count: int
    chunk_count: int
    vector_size: int


def reindex_documents(
    data_dir: str = "data/raw",
    max_chars: int = 300,
    overlap: int = 50,
) -> ReindexResult:
    documents = load_markdown_documents(data_dir)
    chunks = chunk_documents(documents, max_chars=max_chars, overlap=overlap)

    embedding_client = get_embedding_client()
    embeddings = embedding_client.embed_texts([chunk.content for chunk in chunks])
    vector_size = len(embeddings[0])

    vector_store = QdrantVectorStore()
    vector_store.recreate_collection(vector_size=vector_size)
    vector_store.upsert_chunks(chunks, embeddings)

    return ReindexResult(
        document_count=len(documents),
        chunk_count=len(chunks),
        vector_size=vector_size,
    )
