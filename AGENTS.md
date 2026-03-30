# AGENTS.md

## Project goal
Build a Spark AI style RAG assistant using public documentation as a Confluence-like knowledge base.

## Rules
- Prefer simple, readable Python.
- Explain major architecture decisions in comments.
- Do not add heavy abstractions unless requested.
- Use FastAPI for backend APIs.
- Use Qdrant for vector storage.
- Use Mistral for embeddings and answer generation.
- Preserve metadata for every document chunk.
- Add tests for all core pipeline steps.
- Do not change folder structure without explanation.
- When generating code, also explain why the code is needed.