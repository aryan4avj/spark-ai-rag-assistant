# Spark AI RAG Assistant FAQ

This document collects common questions about the Spark AI RAG Assistant project. Use it as a quick technical reference for architecture, RAG concepts, implementation details, deployment, and possible improvements.

## Project Basics

### 1. What problem does this project solve?

It helps users ask natural-language questions over a documentation knowledge base. Instead of manually searching Markdown or Confluence-like pages, the assistant retrieves relevant context and generates a grounded answer with sources.

### 2. What is the core goal of the project?

The core goal is to demonstrate a practical RAG system with a complete path from document ingestion to answer generation. The project covers loading documents, preserving metadata, chunking content, embedding chunks, storing vectors in Qdrant, retrieving relevant context, building prompts, and returning answers through FastAPI.

### 3. What are the main technologies used?

The main technologies are FastAPI, Pydantic, Qdrant, Gemini, Ollama, LangGraph, Docker, Azure Container Apps, and pytest.

### 4. Which model providers does the project support?

The project supports Gemini and Ollama. Gemini is used for hosted embeddings and answer generation. Ollama is available as a local fallback provider path.

### 5. What is the high-level architecture?

The system has an indexing path, a query path, and an agent path. The indexing path turns documents into vectors in Qdrant. The query path retrieves relevant chunks and generates answers. The agent path decides whether to use document retrieval, a calculator tool, or fallback behavior.

## RAG Concepts

### 6. What is RAG?

RAG means retrieval-augmented generation. Before the model generates an answer, the system retrieves relevant external context and includes that context in the prompt. This lets the model answer using project-specific or private information without retraining.

### 7. Why not send all documents directly to the model?

Sending every document does not scale. It can exceed context limits, increase cost, add noise, and reduce answer quality. Retrieval selects only the chunks most likely to answer the question.

### 8. How does RAG reduce hallucination?

RAG reduces hallucination risk by grounding the model in retrieved context. The prompt also instructs the model to answer only from that context and say when the context is insufficient.

### 9. Does RAG completely eliminate hallucinations?

No. RAG reduces unsupported answers, but it does not guarantee perfect faithfulness. Retrieval can return weak context, and the model can still misread or overstate information. That is why citations, tests, and evaluation are important.

### 10. What are common RAG failure modes?

Common failure modes include bad chunking, stale documents, missing metadata, weak embeddings, poor retrieval, irrelevant context, overly broad prompts, model hallucination, vector database outages, and provider API failures.

## Ingestion and Chunking

### 11. What happens during indexing?

The app loads Markdown files from `data/raw`, parses YAML front matter, validates document metadata, chunks the content, generates embeddings, recreates the Qdrant collection, and upserts vectors with metadata payloads.

### 12. Why does the project use Markdown front matter?

Front matter provides structured metadata for each document. This metadata becomes part of the chunk payload and supports source attribution, filtering, debugging, and traceability.

### 13. What metadata is preserved?

Documents preserve metadata such as `doc_id`, `title`, `source`, `source_type`, `space`, `author`, `created_at`, `updated_at`, `tags`, and `url`. Chunks preserve source-related fields plus `section` and `chunk_index`.

### 14. Why is metadata important in RAG?

Metadata makes retrieval inspectable. It lets the system return where a chunk came from, which section it belonged to, and which source supported the answer.

### 15. Why chunk documents?

Chunking improves retrieval precision. Full documents are often too broad, while smaller chunks can represent specific ideas, sections, or facts.

### 16. How does chunking work in this project?

The chunker first splits Markdown by headings, then splits long section text into overlapping character chunks. This preserves document structure while keeping chunks small enough for focused retrieval.

### 17. Why use overlap between chunks?

Overlap reduces the chance of losing important context at chunk boundaries. If relevant information sits near a split point, overlap can keep enough context in both neighboring chunks.

### 18. What could improve the chunking strategy?

Possible improvements include token-aware chunking, paragraph-aware chunking, semantic chunking, configurable chunk size per document type, and neighboring chunk expansion during retrieval.

## Embeddings and Qdrant

### 19. What are embeddings?

Embeddings are dense numeric vectors that represent text meaning. Texts with similar meanings should have vectors that are close together in vector space.

### 20. How are embeddings used here?

Document chunks are embedded during indexing. User questions are embedded during retrieval. Qdrant compares the query vector to stored chunk vectors and returns the closest matches.

### 21. What is Qdrant?

Qdrant is a vector database. It stores vectors, point IDs, and metadata payloads, then supports similarity search over those vectors.

### 22. What does Qdrant store for each chunk?

Qdrant stores the embedding vector, a deterministic point ID, the chunk content, and metadata such as chunk ID, document ID, title, section, source, space, tags, and URL.

### 23. Why use cosine distance?

Cosine distance compares vector direction rather than magnitude. It is commonly used for text embeddings because semantic similarity is often represented by direction in embedding space.

### 24. Why use deterministic UUIDs for Qdrant point IDs?

The point ID is generated from the chunk ID using UUID5. This makes IDs stable across indexing runs for the same chunk IDs.

## Query and Prompting

### 25. What happens when a user calls `/query`?

FastAPI validates the request, the RAG pipeline embeds the question, Qdrant retrieves similar chunks, results are deduplicated, the prompt is built from the chunks, the chat client generates an answer, and the API returns the answer with sources.

### 26. Why does the pipeline search for more raw results than requested?

The pipeline asks Qdrant for `limit * 3` raw results because deduplication may remove repeated chunks from the same document section. Extra candidates make it more likely that the final response has enough unique chunks.

### 27. Why deduplicate by `(doc_id, section)`?

This avoids returning several similar chunks from the same document section. It gives the model more diverse context and makes source lists easier to inspect.

### 28. What is the purpose of `/retrieve`?

`/retrieve` returns retrieved chunks without generating an answer. It is useful for debugging whether retrieval is working before involving the language model.

### 29. What is the purpose of `build_rag_prompt`?

The prompt builder converts the user question and retrieved chunks into a controlled prompt. It instructs the model to answer only from retrieved context and include source numbers.

### 30. What should you check when an answer is bad?

First check `/retrieve`. If the retrieved chunks are bad, debug ingestion, chunking, embeddings, Qdrant, or query wording. If retrieval is good but the answer is bad, debug prompt construction and generation behavior.

## LangGraph Agent

### 31. What does the LangGraph agent add?

The agent adds routing. It can decide whether a question should go to the calculator tool, the RAG document lookup flow, or fallback behavior.

### 32. What are the main agent nodes?

The main nodes are `route_question`, `retrieve_documents`, `call_tool`, `generate_answer`, and `return_fallback`.

### 33. What routes can the agent choose?

Arithmetic-looking questions go to the calculator tool. Empty questions go to fallback. Documentation questions go to RAG retrieval. If retrieval returns chunks, the agent generates an answer. If retrieval returns no chunks, it returns a fallback message.

### 34. Why use LangGraph instead of only regular Python conditionals?

LangGraph makes the flow explicit as a state graph. That makes routing, state updates, tool execution, fallback behavior, and timing easier to reason about and test.

### 35. How is the calculator tool implemented safely?

The calculator extracts arithmetic text, parses it with Python `ast`, and evaluates only allowed numeric and arithmetic nodes. It does not use `eval`.

### 36. What is `timing_ms` in the agent response?

`timing_ms` records the runtime of each graph node. This helps with debugging and performance visibility.

## API and Backend Design

### 37. Why use FastAPI?

FastAPI provides typed request and response handling, automatic OpenAPI docs, simple route composition, and a good testing story through `TestClient`.

### 38. Why use Pydantic?

Pydantic makes request bodies, response bodies, documents, chunks, and metadata explicit and validated. This helps prevent silent shape mismatches across the pipeline.

### 39. Why keep API routes thin?

Thin routes keep HTTP concerns separate from RAG and indexing logic. This makes the core pipeline easier to test without going through HTTP.

### 40. Why use provider factories?

Provider factories isolate model-provider selection. The pipeline can ask for an embedding client or chat client without hardcoding Gemini or Ollama throughout the codebase.

### 41. How would you add another provider?

Add an embedding client and chat client that expose the same methods as the existing clients, add environment variables for the provider, update `app/core/providers.py`, and add provider-selection tests.

## Testing

### 42. What does the default test suite cover?

The default suite covers local document loading, chunking, prompt building, health route behavior, frontend route behavior, admin route authentication, agent graph routing, and agent API response fields.

### 43. Why are integration tests marked separately?

Integration tests require external services such as Qdrant and configured model providers. Keeping them separate makes normal development and CI faster and more reliable.

### 44. How do you run the tests?

Run the default non-integration suite with:

```powershell
pytest
```

Run integration tests with:

```powershell
pytest -m integration
```

### 45. What would improve testing?

Useful improvements include provider factory tests, more vector store tests, retrieval quality checks, a golden question-answer dataset, and answer faithfulness evaluation.

## Deployment and Operations

### 46. How is the project deployed?

The API is packaged as a Docker image, pushed to Azure Container Registry, and deployed to Azure Container Apps. Qdrant runs as a separate Azure Container App.

### 47. Why separate API and Qdrant containers?

The API and vector database have different responsibilities and lifecycles. Separating them lets the API image be rebuilt and deployed without bundling the vector database.

### 48. What did the Azure deployment require for Qdrant?

Qdrant needed internal TCP ingress on port `6333` and explicit binding to `0.0.0.0`. The API uses `QDRANT_URL=http://spark-ai-qdrant:6333`.

### 49. What is `/admin/reindex` for?

`/admin/reindex` rebuilds the Qdrant collection from the bundled Markdown documents. It is protected by the `x-admin-api-key` header.

### 50. Why is manual indexing still useful?

Manual indexing with `scripts/index_chunks.py` is useful for local debugging and learning. The admin endpoint is better for deployed reindexing because it does not require shell access.

## Security and Production Readiness

### 51. What security risks remain?

The public query endpoints are not authenticated, there is no rate limiting, and admin authentication is a shared API key. Production use should add real authentication, authorization, rate limiting, audit logs, and secret rotation.

### 52. What operational risks remain?

Qdrant persistence needs a stronger production setup, reindexing is destructive, cloud deployment is manually documented, and there is no automated answer-quality evaluation.

### 53. How could retrieval quality be improved?

Retrieval could be improved with metadata filters, hybrid keyword plus vector search, reranking, query rewriting, better chunking, and neighboring chunk expansion.

### 54. How could answer quality be evaluated?

Create a dataset of questions, expected sources, and expected answer facts. Measure retrieval precision, source recall, answer faithfulness, and answer completeness.

### 55. What is the difference between retrieval precision and answer faithfulness?

Retrieval precision measures whether the returned chunks are relevant. Answer faithfulness measures whether the generated answer is supported by the retrieved chunks.

## Practical Usage

### 56. How do you start the local stack?

Start Qdrant, index documents, and run the API:

```powershell
docker compose up -d qdrant
python scripts/index_chunks.py
uvicorn app.main:app --reload
```

### 57. How do you ask a local question?

Use Swagger UI at `http://127.0.0.1:8000/docs`, the frontend at `http://127.0.0.1:8000/`, or the helper script:

```powershell
python scripts/ask_rag.py
```

### 58. How do you test the agent calculator route?

Call `POST /agent/query` with:

```json
{
  "question": "What is 12 * (3 + 2)?",
  "top_k": 4
}
```

The expected route is `tool`, and the expected tool is `calculator_tool`.

### 59. How do you test the agent RAG route?

Call `POST /agent/query` with a documentation question such as:

```json
{
  "question": "How does RAG reduce hallucination?",
  "top_k": 2
}
```

The expected route is `rag`, and the expected tool is `doc_lookup_tool`.

### 60. How would you explain the project in one paragraph?

Spark AI RAG Assistant is a FastAPI application that answers questions from a Markdown documentation knowledge base. It indexes documents by parsing metadata, chunking content, embedding chunks, and storing vectors in Qdrant. At query time, it embeds the question, retrieves relevant chunks, builds a grounded prompt, and generates an answer with sources using Gemini or Ollama. It also includes a LangGraph agent that can route between document lookup, a calculator tool, and fallback behavior.
