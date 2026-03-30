from app.generation.prompts import build_rag_prompt
from app.ingestion.local_files import load_markdown_documents
from app.ingestion.chunk import chunk_documents


def test_build_rag_prompt_includes_question_and_context() -> None:
    docs = load_markdown_documents("data/raw")
    chunks = chunk_documents(docs, max_chars=300, overlap=50)[:2]

    question = "What is RAG?"
    prompt = build_rag_prompt(question, chunks)

    assert question in prompt
    assert "Retrieved Context:" in prompt
    assert chunks[0].metadata.title in prompt
    assert chunks[0].content[:20] in prompt
