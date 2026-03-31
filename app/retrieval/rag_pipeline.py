from typing import List, Tuple

from app.core.providers import get_chat_client, get_embedding_client
from app.generation.prompts import build_rag_prompt
from app.schemas.documents import Chunk, ChunkMetadata
from app.vectorstore.qdrant_store import QdrantVectorStore


class RAGPipeline:
    def __init__(self) -> None:
        self.embedding_client = get_embedding_client()
        self.chat_client = get_chat_client()
        self.vector_store = QdrantVectorStore()

    def retrieve(self, question: str, limit: int = 4) -> List[Chunk]:
        query_vector = self.embedding_client.embed_query(question)
        raw_results = self.vector_store.search(query_vector=query_vector, limit=limit * 3)

        chunks: List[Chunk] = []
        seen_keys = set()

        for result in raw_results:
            payload = result.payload

            dedupe_key = (payload["doc_id"], payload.get("section"))
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            chunk = Chunk(
                metadata=ChunkMetadata(
                    chunk_id=payload["chunk_id"],
                    doc_id=payload["doc_id"],
                    title=payload["title"],
                    source=payload["source"],
                    source_type=payload.get("source_type", "local_markdown"),
                    space=payload["space"],
                    section=payload.get("section"),
                    chunk_index=payload["chunk_index"],
                    tags=payload.get("tags", []),
                    url=payload.get("url"),
                ),
                content=payload["content"],
            )
            chunks.append(chunk)

            if len(chunks) >= limit:
                break

        return chunks

    def answer(self, question: str, limit: int = 4) -> Tuple[str, List[Chunk]]:
        chunks = self.retrieve(question=question, limit=limit)
        prompt = build_rag_prompt(question=question, chunks=chunks)
        answer = self.chat_client.generate(prompt)
        return answer, chunks
