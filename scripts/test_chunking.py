from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.local_files import load_markdown_documents
from app.ingestion.chunk import chunk_documents


if __name__ == "__main__":
    docs = load_markdown_documents("data/raw")
    chunks = chunk_documents(docs, max_chars=300, overlap=50)

    print(f"Loaded {len(docs)} documents.")
    print(f"Created {len(chunks)} chunks.\n")

    for chunk in chunks[:12]:
        print(f"chunk_id: {chunk.metadata.chunk_id}")
        print(f"doc_id: {chunk.metadata.doc_id}")
        print(f"title: {chunk.metadata.title}")
        print(f"section: {chunk.metadata.section}")
        print(f"space: {chunk.metadata.space}")
        print(f"content preview: {chunk.content[:150]}")
        print("-" * 80)
