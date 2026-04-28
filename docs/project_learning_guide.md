# Spark AI RAG Assistant Project Guide

Last updated: 2026-04-28

This is the main technical guide for Spark AI RAG Assistant. It explains what the project does, how the system is structured, how data moves through it, and what design choices matter most.

For a question-and-answer reference, see [FAQ.md](FAQ.md).

## 1. Project Purpose

Spark AI RAG Assistant is a documentation assistant built around retrieval-augmented generation. It uses a local Markdown knowledge base as a Confluence-like source of truth, retrieves relevant chunks from that knowledge base, and generates grounded answers with sources.

The project is intentionally small enough to understand end to end, but it includes the main pieces of a real RAG application:

- document loading
- metadata parsing
- chunking
- embedding generation
- vector storage
- semantic retrieval
- prompt construction
- answer generation
- API routes
- a lightweight agent layer
- tests
- Docker packaging
- Azure Container Apps deployment

## 2. Current Provider Support

The project currently supports:

- `gemini` for hosted embeddings and hosted answer generation
- `ollama` for local embeddings and local answer generation

Provider selection is controlled through environment variables:

- `EMBED_PROVIDER`
- `LLM_PROVIDER`

The provider factory in `app/core/providers.py` keeps the rest of the application from hardcoding provider-specific details.

## 3. High-Level System Model

The system has three main runtime paths.

### 3.1 Indexing Path

```text
Markdown files -> front matter parser -> Document objects -> chunks -> embeddings -> Qdrant
```

This path prepares the knowledge base for search.

### 3.2 RAG Query Path

```text
question -> query embedding -> Qdrant search -> retrieved chunks -> prompt -> answer with sources
```

This path answers user questions using retrieved documentation context.

### 3.3 Agent Path

```text
question -> route decision -> calculator tool OR document lookup -> final answer
```

The LangGraph agent is a thin orchestration layer. It can route arithmetic questions to a calculator tool and documentation questions to the RAG pipeline.

## 4. Folder Structure

```text
.
|-- app/
|   |-- agent/         # LangGraph agent and tool routing
|   |-- api/           # FastAPI routes
|   |-- core/          # settings and provider factories
|   |-- embeddings/    # Gemini and Ollama embedding clients
|   |-- generation/    # Gemini and Ollama chat clients, prompt builder
|   |-- ingestion/     # document loading and chunking
|   |-- retrieval/     # RAG pipeline
|   |-- schemas/       # Pydantic models
|   `-- vectorstore/   # Qdrant wrapper
|-- data/raw/          # Markdown knowledge base
|-- docker/            # Dockerfile
|-- docs/              # project guide and FAQ
|-- frontend/          # minimal static UI
|-- scripts/           # local indexing and query helpers
|-- tests/             # unit-ish and integration tests
`-- README.md
```

## 5. Main Components

### 5.1 FastAPI Application

`app/main.py` creates the FastAPI app, registers routers, and serves the frontend from `/`.

Registered routers:

- `app/api/health.py`
- `app/api/query.py`
- `app/api/agent.py`
- `app/api/admin.py`

The API layer is deliberately thin. Routes validate requests and call lower-level pipeline code instead of containing complex business logic.

### 5.2 Configuration

`app/core/config.py` loads environment variables with `python-dotenv` and exposes a `Settings` dataclass.

Important settings:

- `APP_ENV`
- `LOG_LEVEL`
- `ADMIN_API_KEY`
- `LLM_PROVIDER`
- `EMBED_PROVIDER`
- `GEMINI_API_KEY`
- `GEMINI_CHAT_MODEL`
- `GEMINI_EMBED_MODEL`
- `OLLAMA_BASE_URL`
- `OLLAMA_CHAT_MODEL`
- `OLLAMA_EMBED_MODEL`
- `QDRANT_URL`
- `QDRANT_COLLECTION`

This keeps local, Docker, and Azure deployment differences outside the application logic.

### 5.3 Provider Factory

`app/core/providers.py` selects the embedding client and chat client.

Current behavior:

- `EMBED_PROVIDER=gemini` returns `GeminiEmbeddingClient`
- any other embedding provider value falls back to `OllamaEmbeddingClient`
- `LLM_PROVIDER=gemini` returns `GeminiChatClient`
- any other chat provider value falls back to `OllamaChatClient`

This is intentionally simple. It avoids a heavy abstraction while still keeping provider selection centralized.

### 5.4 Ingestion

Ingestion lives in `app/ingestion`.

Important files:

- `local_files.py`
- `chunk.py`
- `indexer.py`

The loader reads Markdown files from `data/raw`, parses YAML front matter, validates metadata with Pydantic, and returns `Document` objects.

The chunker splits documents by Markdown headings first, then splits long sections into overlapping character chunks.

The indexer combines loading, chunking, embedding, collection recreation, and Qdrant upsert into one reusable function.

### 5.5 Vector Store

`app/vectorstore/qdrant_store.py` wraps Qdrant operations.

It handles:

- creating or recreating a collection
- storing chunks and embeddings as Qdrant points
- preserving metadata in point payloads
- searching with a query vector

The collection uses cosine distance for semantic similarity.

### 5.6 RAG Pipeline

`app/retrieval/rag_pipeline.py` is the central query-time orchestrator.

It:

1. embeds the user question
2. searches Qdrant
3. deduplicates results by `(doc_id, section)`
4. converts payloads back into `Chunk` objects
5. builds a RAG prompt
6. calls the configured chat provider
7. returns the answer and source chunks

The retrieval step asks Qdrant for `limit * 3` raw matches because deduplication may remove repeated chunks from the same document section.

### 5.7 Prompt Builder

`app/generation/prompts.py` builds the prompt used for grounded answer generation.

The prompt instructs the model to:

- answer only from retrieved context
- avoid unsupported facts
- say clearly when context is insufficient
- answer concisely
- list source numbers used

This prompt is one of the main controls for answer faithfulness.

### 5.8 LangGraph Agent

`app/agent/graph.py` defines the agent state, tools, and graph.

Main graph nodes:

- `route_question`
- `retrieve_documents`
- `call_tool`
- `generate_answer`
- `return_fallback`

Main routes:

- arithmetic-looking question -> calculator tool
- empty question -> fallback
- documentation question -> RAG retrieval
- retrieval with chunks -> answer generation
- retrieval with no chunks -> fallback

The calculator tool uses Python `ast` and a small allowlist of arithmetic operations. It does not call `eval`.

The agent response includes `timing_ms`, which records how long each graph node took.

## 6. Data Model

The project uses Pydantic models in `app/schemas`.

### 6.1 Document Metadata

Each source document carries metadata such as:

- `doc_id`
- `title`
- `source`
- `source_type`
- `space`
- `author`
- `created_at`
- `updated_at`
- `tags`
- `url`

### 6.2 Chunk Metadata

Each chunk preserves:

- `chunk_id`
- `doc_id`
- `title`
- `source`
- `source_type`
- `space`
- `section`
- `chunk_index`
- `tags`
- `url`

Metadata preservation is critical because retrieval is not enough by itself. The application must also explain where the answer came from.

## 7. API Reference

### `GET /`

Serves the static frontend from `frontend/index.html`.

### `GET /health`

Returns basic health information:

```json
{
  "status": "ok",
  "environment": "local"
}
```

### `POST /retrieve`

Runs retrieval only. This is useful for debugging whether Qdrant is returning the right chunks.

### `POST /query`

Runs the full RAG flow:

```text
request -> retrieve chunks -> build prompt -> generate answer -> return answer and sources
```

### `POST /agent/query`

Runs the LangGraph agent. The response includes:

- selected route
- answer
- sources
- selected tool
- tool result
- per-node timings

### `POST /admin/reindex`

Rebuilds the Qdrant collection from `data/raw`.

This route requires the `x-admin-api-key` header. The value must match `ADMIN_API_KEY`.

## 8. Local Development Workflow

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Index documents:

```powershell
python scripts/index_chunks.py
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Ask through the CLI helper:

```powershell
python scripts/ask_rag.py
```

Inspect retrieval directly:

```powershell
python scripts/search_chunks.py
```

## 9. Docker Workflow

Build the image:

```powershell
docker build -f docker/Dockerfile -t spark-ai-rag-assistant:local .
```

Run the API container:

```powershell
docker run --rm -p 8000:8000 --env-file .env spark-ai-rag-assistant:local
```

Run with Docker Compose:

```powershell
docker compose up -d
```

The Docker image copies the repository into `/app`, including `data/raw`, so the bundled knowledge base is available in the container.

## 10. Testing Strategy

The default test command is:

```powershell
pytest
```

`pytest.ini` excludes integration tests by default:

```text
-m "not integration"
```

Default tests cover:

- document loading
- chunking
- prompt construction
- health endpoint
- frontend route
- admin reindex authentication
- LangGraph agent routing
- agent API response shape

Integration tests cover service-dependent paths such as real retrieval and query behavior. They require running services like Qdrant and configured model providers.

Run integration tests explicitly:

```powershell
pytest -m integration
```

## 11. Azure Deployment

The Azure deployment uses:

- Azure Container Registry
- Azure Container Apps for the API
- Azure Container Apps for Qdrant
- Gemini API for hosted model calls

Current deployed API:

```text
https://spark-ai-api.calmbush-6fb83663.westeurope.azurecontainerapps.io
```

Important API settings:

- `APP_ENV=azure`
- `LLM_PROVIDER=gemini`
- `EMBED_PROVIDER=gemini`
- `GEMINI_API_KEY=secretref:gemini-api-key`
- `QDRANT_URL=http://spark-ai-qdrant:6333`
- `QDRANT_COLLECTION=spark_ai_docs`

Important Qdrant settings:

- internal ingress
- TCP transport
- port `6333`
- listener bound to `0.0.0.0`

Deployment flow:

1. build Docker image
2. push image to Azure Container Registry
3. update the API Container App to the new image
4. validate `/health`
5. validate `/query` or `/agent/query`

## 12. Operational Notes

Several deployment lessons shaped the current setup:

- PowerShell uses backticks for multiline commands, not Bash-style backslashes.
- Explicit Docker image build and push was more reliable than source-based Container Apps deployment for this project.
- Registry authentication is configured separately from image updates.
- The API must run the project image, not the Azure quickstart image.
- Qdrant connectivity in Azure required internal TCP ingress and explicit listener binding.
- Manual indexing is useful for debugging, but `/admin/reindex` is a better operational entry point.

## 13. Known Limitations

- Qdrant persistence needs a stronger production setup.
- Reindexing recreates the collection, which is simple but destructive.
- Chunking is character-based rather than token-aware.
- Retrieval does not yet use hybrid search or reranking.
- Public query endpoints do not yet have user authentication.
- There is no automated answer-quality evaluation harness.
- Azure infrastructure is documented manually rather than managed through infrastructure as code.

## 14. Future Improvements

Good next steps:

- add persistent Qdrant storage or managed Qdrant
- add incremental indexing
- add scheduled reindex jobs
- add metadata filtering
- add hybrid search
- add a reranker
- add a retrieval and answer evaluation dataset
- add authentication and rate limiting
- add richer frontend source navigation
- add infrastructure as code for Azure resources

## 15. Compact Mental Model

Remember the project as two core loops and one optional agent layer.

Indexing loop:

```text
documents -> chunks -> embeddings -> Qdrant
```

Answering loop:

```text
question -> query embedding -> retrieval -> prompt -> answer
```

Agent layer:

```text
question -> route -> tool or RAG -> answer
```

That model is enough to explain most of the codebase and to debug most failures.
