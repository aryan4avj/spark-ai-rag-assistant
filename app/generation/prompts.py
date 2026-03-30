from typing import List

from app.schemas.documents import Chunk


def build_rag_prompt(question: str, chunks: List[Chunk]) -> str:
    context_blocks = []

    for i, chunk in enumerate(chunks, start=1):
        block = (
            f"[Source {i}]\n"
            f"Title: {chunk.metadata.title}\n"
            f"Section: {chunk.metadata.section}\n"
            f"Space: {chunk.metadata.space}\n"
            f"Content:\n{chunk.content}"
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)

    prompt = f"""
You are a helpful internal knowledge assistant.

Answer the user's question using only the provided context.
If the answer is not supported by the context, say clearly that the answer is not available in the retrieved documents.
Do not invent facts.
Be concise but useful.
At the end, include a short "Sources Used" section listing the source numbers you relied on.

User Question:
{question}

Retrieved Context:
{context_text}

Answer:
""".strip()

    return prompt
