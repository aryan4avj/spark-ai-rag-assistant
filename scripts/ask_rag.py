from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.retrieval.rag_pipeline import RAGPipeline


if __name__ == "__main__":
    question = "How does RAG reduce hallucination?"

    pipeline = RAGPipeline()
    answer, chunks = pipeline.answer(question=question, limit=4)

    print(f"\nQuestion: {question}\n")
    print("Answer:")
    print(answer)
    print("\nRetrieved Sources:")
    for i, chunk in enumerate(chunks, start=1):
        print(f"{i}. {chunk.metadata.title} | {chunk.metadata.section} | {chunk.metadata.doc_id}")
