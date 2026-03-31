import pytest

from app.retrieval.rag_pipeline import RAGPipeline

pytestmark = pytest.mark.integration


def test_retrieve_returns_limited_results() -> None:
    pipeline = RAGPipeline()
    chunks = pipeline.retrieve("How does RAG reduce hallucination?", limit=3)

    assert len(chunks) <= 3
    assert len(chunks) > 0


def test_retrieve_deduplicates_doc_section_pairs() -> None:
    pipeline = RAGPipeline()
    chunks = pipeline.retrieve("How does RAG reduce hallucination?", limit=4)

    seen = set()
    for chunk in chunks:
        key = (chunk.metadata.doc_id, chunk.metadata.section)
        assert key not in seen
        seen.add(key)
