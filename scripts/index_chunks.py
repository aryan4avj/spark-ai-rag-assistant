from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.indexer import reindex_documents


if __name__ == "__main__":
    print("Loading documents...")
    print("Chunking documents...")
    print("Generating embeddings...")
    print("Recreating Qdrant collection...")
    result = reindex_documents()
    print(f"Created {result.chunk_count} chunks.")
    print(f"Embedding dimension: {result.vector_size}")
    print("Upserting chunks into Qdrant...")
    print("Done. Chunks indexed successfully.")
