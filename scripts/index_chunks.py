from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.providers import get_embedding_client
from app.ingestion.chunk import chunk_documents
from app.ingestion.local_files import load_markdown_documents
from app.vectorstore.qdrant_store import QdrantVectorStore


if __name__ == "__main__":
    print("Loading documents...")
    documents = load_markdown_documents("data/raw")

    print("Chunking documents...")
    chunks = chunk_documents(documents, max_chars=300, overlap=50)
    print(f"Created {len(chunks)} chunks.")

    embedding_client = get_embedding_client()

    print("Generating embeddings...")
    embeddings = embedding_client.embed_texts([chunk.content for chunk in chunks])

    vector_size = len(embeddings[0])
    print(f"Embedding dimension: {vector_size}")

    vector_store = QdrantVectorStore()

    print("Recreating Qdrant collection...")
    vector_store.recreate_collection(vector_size=vector_size)

    print("Upserting chunks into Qdrant...")
    vector_store.upsert_chunks(chunks, embeddings)

    print("Done. Chunks indexed successfully.")
