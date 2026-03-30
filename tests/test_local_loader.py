from app.ingestion.local_files import load_markdown_documents


def test_load_markdown_documents() -> None:
    docs = load_markdown_documents("data/raw")

    assert len(docs) >= 8

    doc_ids = {doc.metadata.doc_id for doc in docs}
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

    first_doc = docs[0]
    assert first_doc.metadata.doc_id
    assert first_doc.metadata.title
    assert first_doc.content
