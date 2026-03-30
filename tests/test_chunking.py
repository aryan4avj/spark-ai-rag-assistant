from app.ingestion.chunk import chunk_document, chunk_documents, split_markdown_sections
from app.ingestion.local_files import load_markdown_documents


def test_split_markdown_sections() -> None:
    content = """# Title

Intro text.

## Section One

This is section one.

## Section Two

This is section two.
"""
    sections = split_markdown_sections(content)

    assert len(sections) == 3
    assert sections[0][0] == "Title"
    assert sections[1][0] == "Section One"
    assert sections[2][0] == "Section Two"


def test_chunk_document_creates_chunks() -> None:
    docs = load_markdown_documents("data/raw")
    doc = docs[0]

    chunks = chunk_document(doc, max_chars=300, overlap=50)

    assert len(chunks) > 0
    assert chunks[0].metadata.doc_id == doc.metadata.doc_id
    assert chunks[0].metadata.chunk_id
    assert chunks[0].content


def test_chunk_documents_creates_flat_chunk_list() -> None:
    docs = load_markdown_documents("data/raw")
    chunks = chunk_documents(docs, max_chars=300, overlap=50)

    assert len(chunks) >= len(docs)

    doc_ids = {chunk.metadata.doc_id for chunk in chunks}
    expected_ids = {
        "ai-001",
        "ai-002",
        "ai-003",
        "eng-001",
        "eng-002",
        "plat-001",
        "plat-002",
        "prod-001",
    }
    assert expected_ids.issubset(doc_ids)
