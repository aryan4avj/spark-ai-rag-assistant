from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.providers import get_embedding_client
from app.vectorstore.qdrant_store import QdrantVectorStore


if __name__ == "__main__":
    query = "How does RAG reduce hallucination?"

    embedding_client = get_embedding_client()
    vector_store = QdrantVectorStore()

    print(f"Query: {query}")
    query_vector = embedding_client.embed_query(query)

    results = vector_store.search(query_vector=query_vector, limit=5)

    print(f"\nTop {len(results)} results:\n")
    for i, result in enumerate(results, start=1):
        payload = result.payload
        print(f"Rank: {i}")
        print(f"Score: {result.score}")
        print(f"Doc ID: {payload.get('doc_id')}")
        print(f"Title: {payload.get('title')}")
        print(f"Section: {payload.get('section')}")
        print(f"Space: {payload.get('space')}")
        print(f"Content Preview: {payload.get('content', '')[:200]}")
        print("-" * 80)
