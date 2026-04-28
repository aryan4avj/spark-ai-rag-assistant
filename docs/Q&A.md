# Spark AI RAG Assistant Interview Prep Guide

Use this guide to prepare for explaining the project in an interview. It is written around the current repository state, including the newer LangGraph-based agent layer.

## 1. One-Minute Project Pitch

Spark AI RAG Assistant is a FastAPI-based retrieval-augmented generation application that answers questions from a small Confluence-style knowledge base stored as local Markdown files.

The system ingests documents from `data/raw`, parses their front matter metadata, splits the content into smaller chunks, generates embeddings, stores those vectors in Qdrant, retrieves the most relevant chunks for a user question, builds a grounded prompt, and asks the configured chat provider to generate an answer with sources.

The project also includes an agent endpoint powered by LangGraph. The agent can route arithmetic questions to a calculator tool and documentation questions to the RAG retrieval flow.

Good interview framing:

> I built a production-style learning project for a documentation assistant. It covers the full RAG lifecycle: ingestion, chunking, metadata preservation, vector indexing, semantic retrieval, prompt construction, answer generation, API design, tests, Docker packaging, and deployment-oriented configuration.

## 2. The Big Mental Model

There are two main loops.

### Indexing loop

```text
Markdown docs -> front matter parser -> Document objects -> chunks -> embeddings -> Qdrant
```

This loop prepares the knowledge base for search.

### Answering loop

```text
question -> query embedding -> Qdrant similarity search -> retrieved chunks -> prompt -> LLM answer -> sources
```

This loop happens whenever a user asks a question.

### Agent loop

```text
question -> route decision -> calculator OR document retrieval -> final answer/fallback
```

The agent layer is a thin orchestration layer on top of the existing RAG pipeline. It does not replace RAG; it decides when to use RAG.

## 3. Folder Map

| Path | Purpose |
| --- | --- |
| `app/main.py` | Creates the FastAPI app, includes routers, serves the frontend |
| `app/api/` | HTTP route handlers for health, query, admin, and agent APIs |
| `app/core/config.py` | Loads environment variables into a settings object |
| `app/core/providers.py` | Selects embedding and chat providers |
| `app/ingestion/` | Loads Markdown files and chunks documents |
| `app/embeddings/` | Provider clients for embedding generation |
| `app/vectorstore/qdrant_store.py` | Qdrant wrapper for collection, upsert, and search |
| `app/retrieval/rag_pipeline.py` | Runtime RAG orchestration |
| `app/generation/prompts.py` | Builds grounded prompts from retrieved chunks |
| `app/agent/graph.py` | LangGraph agent routing and tool flow |
| `app/schemas/` | Pydantic models for documents and API responses |
| `frontend/index.html` | Minimal browser UI |
| `scripts/` | CLI helpers for indexing, searching, and asking questions |
| `tests/` | Unit-ish tests plus integration tests |

## 4. Key Technologies and Why They Are Used

### FastAPI

FastAPI exposes the system as a clean HTTP API. It gives request validation, automatic OpenAPI docs, typed request and response models, and a simple way to organize routes.

Main endpoints:

- `GET /health`
- `POST /retrieve`
- `POST /query`
- `POST /agent/query`
- `POST /admin/reindex`
- `GET /` for the static frontend

Interview answer:

> I used FastAPI because this project benefits from typed API contracts, simple route composition, built-in docs, and easy testing through TestClient.

### Pydantic

Pydantic models define documents, chunks, metadata, query requests, and API responses. This keeps the boundary between raw data and validated application objects clear.

Important models:

- `DocumentMetadata`
- `Document`
- `ChunkMetadata`
- `Chunk`
- `QueryRequest`
- `QueryResponse`
- `AgentQueryResponse`

Interview answer:

> Pydantic helps keep the data shape explicit. In a RAG system, metadata correctness matters because citations, filtering, debugging, and source traceability all depend on it.

### Qdrant

Qdrant stores vector embeddings and metadata payloads. The project uses cosine distance for semantic similarity search.

Stored per chunk:

- vector embedding
- deterministic point ID
- chunk ID
- document ID
- title
- source
- source type
- space
- section
- chunk index
- tags
- URL
- chunk content

Interview answer:

> Qdrant is the vector database boundary. The app stores each chunk vector together with metadata, then searches by query vector to find semantically similar chunks.

### Embeddings

Embeddings convert text into dense vectors. Similar meanings should land near each other in vector space.

In this project:

- document chunks are embedded during indexing
- user questions are embedded during retrieval
- Qdrant compares the query vector against stored chunk vectors

Interview answer:

> Embeddings make semantic search possible. Instead of exact keyword matching, the system can retrieve text that is conceptually related to the question.

### Gemini and Ollama provider paths

The current code supports `gemini` and `ollama` through provider factories. The repo instructions mention Mistral as a project preference, but the current implementation uses Gemini/Ollama. A good interview answer is to call this out calmly:

> The provider boundary is already isolated in `app/core/providers.py`, so adding a Mistral implementation would mean adding Mistral embedding/chat clients and routing to them from the provider factory. The rest of the pipeline should not need major changes.

### LangGraph

LangGraph is used in `app/agent/graph.py` to model the agent as a state machine.

Current graph nodes:

- `route_question`
- `retrieve_documents`
- `call_tool`
- `generate_answer`
- `return_fallback`

Current routes:

- arithmetic-looking question -> calculator tool
- empty question -> fallback
- normal question -> RAG retrieval
- retrieval with chunks -> answer generation
- retrieval with no chunks -> fallback

Interview answer:

> I used LangGraph to make the agent flow explicit as a graph of nodes and conditional edges. That makes routing behavior easier to test than a hidden chain of if-statements spread across the API.

### Docker

Docker packages the API, source code, dependencies, scripts, and local `data/raw` documents into a runnable image.

Interview answer:

> Docker gives a repeatable runtime. It also helped validate that the data files were actually present in the deployed container image.

### Azure Container Apps

The README documents an Azure Container Apps deployment with one app for the FastAPI API and one internal app for Qdrant.

Interview answer:

> The API and Qdrant are separated as services. The API talks to Qdrant through an environment-configured URL, which makes local and cloud deployments use the same application code.

## 5. Indexing Flow in Detail

Entry points:

- `python scripts/index_chunks.py`
- `POST /admin/reindex`

Core implementation:

- `app/ingestion/indexer.py`

Step by step:

1. `load_markdown_documents("data/raw")` recursively loads Markdown files.
2. `parse_front_matter` extracts YAML front matter and body content.
3. `DocumentMetadata(**metadata_dict)` validates the metadata.
4. `chunk_documents` turns documents into chunks.
5. The embedding client embeds each chunk's content.
6. The vector size is inferred from the first embedding.
7. Qdrant collection is recreated with that vector size and cosine distance.
8. Chunks and embeddings are upserted into Qdrant.
9. A `ReindexResult` returns document count, chunk count, and vector size.

Why this design is useful:

- indexing is reusable from CLI and API
- metadata is preserved at every step
- collection recreation gives a clean development workflow
- vector size is provider-driven instead of hardcoded

Tradeoff:

- recreating the collection is simple, but it is destructive. In production you might prefer incremental indexing, versioned collections, or blue-green index swaps.

## 6. Chunking Flow in Detail

Main file:

- `app/ingestion/chunk.py`

The project first splits Markdown by headings using `split_markdown_sections`. It recognizes heading levels `#`, `##`, and `###`.

Then each section is split by character length using `split_text_with_overlap`.

Default reindex values:

- `max_chars=300`
- `overlap=50`

Why chunking matters:

- whole documents may be too large and noisy
- smaller chunks improve retrieval precision
- overlap reduces the chance of splitting important context across boundaries
- section metadata helps citations and debugging

Possible improvement:

- token-aware chunking instead of character-aware chunking
- semantic chunking by paragraphs or headings
- configurable chunk settings per document type

Interview answer:

> I chunk by Markdown section first, then by character length with overlap. This preserves document structure while keeping chunks small enough for focused retrieval.

## 7. Query Flow in Detail

Endpoint:

- `POST /query`

Files:

- `app/api/query.py`
- `app/retrieval/rag_pipeline.py`
- `app/generation/prompts.py`

Step by step:

1. FastAPI validates `QueryRequest`.
2. The route calls `pipeline.answer(question, limit=top_k)`.
3. The pipeline embeds the question.
4. Qdrant searches for similar vectors.
5. The pipeline asks for `limit * 3` raw results.
6. Results are deduplicated by `(doc_id, section)`.
7. The top unique chunks are converted into `Chunk` objects.
8. `build_rag_prompt` inserts the question and retrieved chunks into a controlled prompt.
9. The chat client generates the final answer.
10. The API returns the answer plus normalized source objects.

Why `limit * 3` is used:

> The search asks for extra raw results because deduplication may remove repeated chunks from the same document section. Asking for more candidates increases the chance of returning the requested number of unique chunks.

Why dedupe by `(doc_id, section)`:

> It avoids showing several near-duplicate chunks from the same section and gives the model more diverse context.

Tradeoff:

> This dedupe strategy may hide useful adjacent chunks from the same section. For long sections, a future version might dedupe less aggressively or support neighboring chunk expansion.

## 8. Prompting Strategy

Main file:

- `app/generation/prompts.py`

The prompt tells the model:

- answer only from retrieved context
- do not invent facts
- say clearly when unsupported
- answer in 3 to 6 sentences
- include `Sources Used:` with source numbers

Why this matters:

- RAG quality depends on both retrieval and generation
- the prompt turns raw chunks into a grounded answer task
- source numbering makes answers inspectable

Interview answer:

> The prompt is intentionally strict. It reduces unsupported answers by telling the model to use only retrieved context and cite the source numbers it relied on.

## 9. Agent Flow in Detail

Endpoint:

- `POST /agent/query`

Files:

- `app/api/agent.py`
- `app/agent/graph.py`

State fields:

- `question`
- `top_k`
- `route`
- `retrieved_chunks`
- `tool_name`
- `tool_result`
- `answer`
- `timing_ms`

The graph:

```text
route_question
  -> rag      -> retrieve_documents -> generate_answer OR return_fallback
  -> tool     -> call_tool
  -> fallback -> return_fallback
```

Calculator tool:

- extracts arithmetic characters using regex
- parses the expression with Python `ast`
- evaluates only allowed arithmetic nodes
- rejects unsupported syntax

Why the calculator uses `ast` instead of `eval`:

> `eval` would execute arbitrary Python code. The calculator parses the expression into an AST and only allows numeric constants, arithmetic operators, and unary operators. That keeps the tool small and safer.

Why LangGraph is useful here:

- explicit routing
- testable nodes
- shared state
- timing information per node
- easier extension with future tools

Possible future agent tools:

- metadata-filtered search tool
- reindex status tool
- web/document ingestion tool
- escalation/fallback tool
- query rewriting tool

## 10. API Endpoints to Remember

### `GET /health`

Returns:

- `status`
- `environment`

Used for deployment checks.

### `POST /retrieve`

Returns retrieved chunks without generating an answer.

Good for debugging retrieval quality.

### `POST /query`

Runs full RAG answer generation.

### `POST /agent/query`

Runs the LangGraph agent. It returns route, answer, sources, selected tool, tool result, and timings.

### `POST /admin/reindex`

Protected by `x-admin-api-key`.

Used to rebuild the Qdrant index from bundled Markdown documents.

## 11. Configuration to Know

Main file:

- `app/core/config.py`

Important environment variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Runtime environment label |
| `LOG_LEVEL` | Logging level |
| `ADMIN_API_KEY` | Protects admin reindex endpoint |
| `LLM_PROVIDER` | Selects chat provider |
| `EMBED_PROVIDER` | Selects embedding provider |
| `OLLAMA_BASE_URL` | Ollama API URL |
| `OLLAMA_EMBED_MODEL` | Ollama embedding model |
| `OLLAMA_CHAT_MODEL` | Ollama chat model |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_CHAT_MODEL` | Gemini chat model |
| `GEMINI_EMBED_MODEL` | Gemini embedding model |
| `QDRANT_URL` | Qdrant HTTP endpoint |
| `QDRANT_COLLECTION` | Qdrant collection name |

Interview answer:

> Configuration is environment-driven so the same code can run locally, in Docker, or in Azure with different providers and service URLs.

## 12. Testing Strategy

The default test command is:

```powershell
pytest
```

The current default suite excludes integration tests through `pytest.ini`.

Current fast coverage includes:

- admin API authentication behavior
- agent graph routing
- agent API response fields
- chunking
- frontend route
- health route
- local document loading
- prompt construction

Integration tests are marked with `pytest.mark.integration` and include:

- real retrieval pipeline behavior
- real `/retrieve` and `/query` behavior

Why integration tests are excluded by default:

> They depend on external services such as Qdrant and model providers. Keeping them separate makes local and CI feedback faster and more stable.

Recent local result on this workspace:

```text
14 passed, 4 deselected
```

## 13. Demo Script for an Interview

Use this flow if asked to show the project.

1. Start Qdrant:

```powershell
docker compose up -d qdrant
```

2. Reindex documents:

```powershell
python scripts/index_chunks.py
```

3. Start API:

```powershell
uvicorn app.main:app --reload
```

4. Open docs:

```text
http://127.0.0.1:8000/docs
```

5. Ask:

```json
{
  "question": "How does RAG reduce hallucination?",
  "top_k": 4
}
```

6. Show retrieval-only debugging:

```text
POST /retrieve
```

7. Show agent routing:

```json
{
  "question": "What is 12 * (3 + 2)?",
  "top_k": 4
}
```

Expected agent route:

```text
tool -> calculator_tool
```

8. Show normal agent RAG:

```json
{
  "question": "What are common RAG failure modes?",
  "top_k": 4
}
```

Expected agent route:

```text
rag -> doc_lookup_tool -> generate_answer
```

## 14. Strong Design Decisions to Explain

### Thin API routes

Routes validate HTTP input and call pipeline logic. They do not contain deep business logic.

Why it matters:

> It keeps HTTP concerns separate from RAG concerns.

### Provider factories

Provider selection lives in `app/core/providers.py`.

Why it matters:

> The pipeline can call `get_embedding_client()` and `get_chat_client()` without knowing whether the implementation is Gemini, Ollama, or a future Mistral client.

### Metadata preservation

Every chunk keeps document metadata.

Why it matters:

> Without metadata, the system could retrieve text but could not explain where the answer came from.

### Retrieval-only endpoint

`POST /retrieve` lets you inspect search results without LLM generation.

Why it matters:

> It separates retrieval debugging from generation debugging.

### Admin reindex endpoint

`POST /admin/reindex` reuses the same indexing logic as the CLI script.

Why it matters:

> It gives an operational path for rebuilding the index after deployment.

### LangGraph agent

The agent graph separates route decision, tool execution, retrieval, generation, and fallback.

Why it matters:

> It makes agent behavior visible, testable, and easier to extend.

## 15. Known Limitations and Honest Tradeoffs

Use these if asked what you would improve.

### No persistent Qdrant storage documented for production

If Qdrant runs without persistent storage, vectors may be lost when the container restarts.

Improvement:

- attach persistent volume storage
- use managed Qdrant Cloud
- rebuild index automatically on deployment

### Reindexing is destructive

The current flow recreates the collection.

Improvement:

- incremental indexing
- versioned collections
- background indexing jobs
- blue-green collection swap

### Character-based chunking

The current chunking is simple and readable.

Improvement:

- token-aware chunking
- paragraph-aware chunking
- semantic chunking

### No reranker

The system uses vector similarity directly.

Improvement:

- add a reranker after Qdrant retrieval
- use hybrid search for exact keywords plus semantic search

### Minimal auth

Only admin reindex has an API key.

Improvement:

- user authentication
- role-based access
- rate limiting
- audit logs

### No evaluation harness

Tests verify code paths, but not answer quality.

Improvement:

- golden question-answer dataset
- retrieval precision checks
- answer faithfulness checks
- regression scoring

### Provider mismatch with stated goal

The project instructions mention Mistral, but current code uses Gemini/Ollama.

Improvement:

- add `MistralEmbeddingClient`
- add `MistralChatClient`
- update provider factory
- add tests for provider selection

## 16. Interview Questions and Model Answers

### 1. What problem does this project solve?

It helps users ask natural-language questions over internal documentation. Instead of searching manually through Markdown or Confluence-like docs, the assistant retrieves relevant context and generates a grounded answer with sources.

### 2. What is RAG?

RAG means Retrieval-Augmented Generation. Before the model answers, the system retrieves relevant external context and includes that context in the prompt. This helps the model answer from current or private knowledge without retraining.

### 3. Why not just send all documents to the LLM?

That does not scale. Documents may exceed context limits, cost more, add noise, and reduce answer quality. Retrieval selects only the most relevant chunks.

### 4. What happens during indexing?

The app loads Markdown files, parses YAML front matter, validates metadata, splits content into chunks, embeds each chunk, recreates the Qdrant collection, and upserts vectors with metadata payloads.

### 5. What happens when a user asks a question?

The question is embedded, Qdrant retrieves similar chunks, duplicate document-section pairs are removed, the prompt is built from the remaining chunks, and the chat model generates an answer with source numbers.

### 6. Why preserve metadata?

Metadata supports citations, filtering, debugging, and traceability. It lets the API return title, section, space, doc ID, source, and URL along with each answer.

### 7. What is a vector database?

A vector database stores embeddings and supports nearest-neighbor similarity search. In this project, Qdrant stores vectors plus metadata payloads for each chunk.

### 8. Why use cosine distance?

Cosine distance compares vector direction rather than raw magnitude. It is commonly used for text embeddings because semantic similarity is often represented by direction in embedding space.

### 9. Why chunk documents?

Chunking makes retrieval more precise. If a whole document is embedded as one vector, the result can be too broad. Smaller chunks let the system retrieve the section that actually answers the question.

### 10. Why use overlap?

Overlap reduces the chance of losing context at chunk boundaries. If an important sentence spans a boundary, overlap may keep enough context in both neighboring chunks.

### 11. Why split by Markdown headings first?

Headings preserve document structure. The chunk can carry a meaningful section name, which improves citations and makes debugging easier.

### 12. What is the role of `RAGPipeline`?

`RAGPipeline` is the runtime orchestrator. It owns the embedding client, chat client, and vector store, and coordinates retrieval and answer generation.

### 13. Why have `/retrieve` and `/query` separately?

`/retrieve` helps debug search quality without involving the LLM. `/query` runs the full answer-generation path. This separation makes troubleshooting easier.

### 14. What is the purpose of `build_rag_prompt`?

It converts the user question and retrieved chunks into a clear instruction for the chat model. It tells the model to answer only from context and include source references.

### 15. How does the system reduce hallucinations?

It grounds the model in retrieved context, gives strict prompt rules, and returns sources. This does not eliminate hallucinations completely, but it reduces unsupported answers and makes them easier to inspect.

### 16. What happens if retrieval returns no chunks?

The normal RAG pipeline would still build a prompt with empty context. The agent path explicitly falls back with a message saying it could not find enough reliable documentation context.

### 17. What is LangGraph doing here?

LangGraph models the agent as a state graph. It routes questions to either document retrieval, a calculator tool, or fallback, then returns a final state.

### 18. Why add an agent if the RAG pipeline already works?

The agent adds decision-making. It can choose tools for questions that are not best answered by document retrieval, such as arithmetic. It also creates a path for adding more tools later.

### 19. How is the calculator tool made safer?

It does not use `eval`. It parses the expression with `ast` and only allows numeric constants and arithmetic operators.

### 20. What is `timing_ms` in the agent response?

It records how long each graph node took. This helps with debugging and performance visibility.

### 21. Why use provider factories?

Provider factories isolate model-provider selection. The rest of the application does not need to know whether embeddings or chat responses come from Gemini, Ollama, or a future provider.

### 22. How would you add Mistral?

I would add Mistral embedding and chat clients with the same methods as the existing clients, update `get_embedding_client` and `get_chat_client`, add environment variables, and write tests for provider selection.

### 23. What does Qdrant store besides vectors?

It stores payload metadata such as chunk ID, document ID, title, source, space, section, tags, URL, and content.

### 24. Why use deterministic UUIDs for point IDs?

The point ID is generated from the chunk ID using UUID5. This makes IDs stable across indexing runs for the same chunk IDs.

### 25. What are integration tests in this project?

Integration tests are tests that require external services such as Qdrant or model providers. They are marked with `pytest.mark.integration` and excluded from the default suite.

### 26. Why exclude integration tests by default?

They are slower and less deterministic because they depend on external services. Excluding them keeps normal development and CI faster.

### 27. How does the admin reindex endpoint work?

It checks the `x-admin-api-key` header, calls the shared `reindex_documents` function, and returns counts for documents, chunks, and vector size.

### 28. What security risks remain?

The public query APIs are not authenticated, there is no rate limiting, and admin auth is a simple shared key. For production, I would add proper auth, authorization, rate limits, secret rotation, and audit logging.

### 29. How would you improve retrieval quality?

I would add hybrid search, metadata filters, a reranker, better chunking, query rewriting, neighboring chunk expansion, and evaluation datasets to measure retrieval quality.

### 30. How would you evaluate answer quality?

I would create a test set of questions, expected sources, and expected answer facts. Then I would measure retrieval precision, source recall, faithfulness, and answer completeness.

### 31. What is the difference between retrieval precision and answer faithfulness?

Retrieval precision measures whether the retrieved chunks are relevant. Answer faithfulness measures whether the generated answer is actually supported by those chunks.

### 32. What could go wrong in a RAG system?

Bad chunking, stale docs, missing metadata, low-quality embeddings, poor retrieval, irrelevant context, prompt leakage, model hallucination, unavailable vector database, and provider API failures.

### 33. How would you debug a bad answer?

First call `/retrieve` to inspect retrieved chunks. If chunks are bad, debug ingestion, chunking, embeddings, or search. If chunks are good but answer is bad, debug prompt construction and model behavior.

### 34. Why is Docker useful here?

It makes the runtime repeatable and packages the app with dependencies and data files. It also supports local compose and cloud deployment.

### 35. Why separate API and Qdrant containers?

They have different responsibilities and lifecycles. The API can be rebuilt and deployed independently from the vector database.

### 36. What did Azure deployment teach?

Service health does not always mean service reachability. Qdrant needed correct internal TCP ingress and listener settings before the API could reach it reliably.

### 37. What would you change before production?

I would add persistent Qdrant storage, real auth, rate limiting, structured logging, monitoring, automated deployment, scheduled indexing, evaluation, and safer index versioning.

### 38. Why is the frontend intentionally simple?

The project is backend and RAG focused. The minimal frontend proves browser usability without adding unnecessary framework complexity.

### 39. What is the most important engineering lesson from this project?

A useful AI app is not just a model call. It requires data ingestion, retrieval, metadata, prompt design, APIs, testing, deployment, and operations.

### 40. How would you explain this project to a non-technical interviewer?

It is like a smart search assistant for company documentation. It first finds the most relevant pages, then writes a short answer based only on those pages and shows where the answer came from.

## 17. Questions You Should Be Ready to Ask the Interviewer

Use these to sound thoughtful.

- How do you currently evaluate RAG answer quality?
- Do you use hybrid search, reranking, or metadata filtering?
- How do you handle document freshness and reindexing?
- What vector database or retrieval stack do you use?
- How do you measure hallucination or answer faithfulness?
- What are the main production failure modes your AI systems face?
- How do you handle access control for private documents in RAG?

## 18. Short Revision Checklist

Before the interview, make sure you can explain:

- what RAG is
- why chunking is needed
- what embeddings are
- why metadata matters
- how Qdrant is used
- what FastAPI endpoints exist
- how indexing works
- how querying works
- how the LangGraph agent routes questions
- what tests exist
- what production improvements are needed
- how you would add Mistral
- how you would debug bad retrieval
- how you would evaluate answer quality

## 19. Best Final Interview Summary

If you only remember one answer, use this:

> Spark AI RAG Assistant is a full-stack learning project for a documentation assistant. I built the ingestion path that loads Markdown docs, preserves metadata, chunks content, embeds chunks, and stores them in Qdrant. I built the query path that embeds a question, retrieves relevant chunks, constructs a grounded prompt, and returns an answer with sources through FastAPI. I also added a LangGraph agent that can route between document lookup and a calculator tool. The main engineering focus was keeping the system simple, testable, configurable, and honest about limitations like persistence, auth, evaluation, and production indexing.
