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

Rules:
- Answer only using the retrieved context below.
- Do not invent facts or add outside knowledge.
- If the answer is not supported by the context, say that clearly.
- Write a direct, useful answer in 3 to 6 sentences.
- After the answer, add a line starting with "Sources Used:" and list only the source numbers you relied on, like [1], [2].

User Question:
{question}

Retrieved Context:
{context_text}

Answer:
""".strip()

    return prompt