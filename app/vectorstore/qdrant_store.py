from typing import List
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.schemas.documents import Chunk


class QdrantVectorStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection

    def recreate_collection(self, vector_size: int) -> None:
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings length mismatch.")

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            payload = {
                "chunk_id": chunk.metadata.chunk_id,
                "doc_id": chunk.metadata.doc_id,
                "title": chunk.metadata.title,
                "source": chunk.metadata.source,
                "source_type": chunk.metadata.source_type,
                "space": chunk.metadata.space,
                "section": chunk.metadata.section,
                "chunk_index": chunk.metadata.chunk_index,
                "tags": chunk.metadata.tags,
                "url": chunk.metadata.url,
                "content": chunk.content,
            }

            point_id = str(uuid5(NAMESPACE_URL, chunk.metadata.chunk_id))

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(self, query_vector: List[float], limit: int = 5):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
        )
        return response.points
