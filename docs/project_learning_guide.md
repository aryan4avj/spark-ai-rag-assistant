# Spark AI RAG Assistant Learning Guide

Version: 9588479

## 1. Purpose of This Document

This guide explains the project end to end for learning purposes. It is intentionally more detailed than the README. The goal is to help you understand not only what the system does, but also why each piece exists, how the pieces connect, how the project evolved, and what operational problems showed up during deployment.

If you come back to this project after a gap, this document should help you rebuild the mental model quickly.

## 2. Project Goal

The project is a Retrieval-Augmented Generation (RAG) assistant built with FastAPI. It ingests markdown documentation, chunks it into searchable units, embeds those chunks into vectors, stores those vectors in Qdrant, retrieves relevant chunks for a user question, and then generates a grounded answer with cited sources.

The system started as a local-learning backend and then evolved into a cloud-deployed application on Azure Container Apps.

The final system supports:

- local indexing from markdown files under `data/raw`
- vector storage with Qdrant
- provider-aware LLM and embedding selection
- Gemini support for both chat and embeddings
- a FastAPI API layer
- a protected admin reindex endpoint
- a minimal frontend for asking questions
- Docker-based deployment
- CI for non-integration tests

## 3. What RAG Means in This Project

Large language models are good at generating text, but they do not automatically know the project documents you care about. RAG solves that by inserting a retrieval step before generation.

In this project, the sequence is:

1. Read the markdown knowledge base.
2. Split it into chunks while preserving metadata.
3. Convert each chunk into an embedding vector.
4. Store those vectors in Qdrant.
5. When a question arrives, embed the question.
6. Search Qdrant for the most similar stored chunks.
7. Build a prompt using those chunks.
8. Ask the chat model to answer only from the retrieved context.
9. Return the answer plus sources.

This design matters because it makes the answer more grounded and inspectable than a plain LLM call.

## 4. High-Level Architecture

### 4.1 Core flow

Knowledge base:

`data/raw/*.md` -> loader -> chunker -> embedding client -> Qdrant

Question answering:

user question -> FastAPI `/query` -> RAG pipeline -> embedding client -> Qdrant search -> prompt builder -> chat client -> answer + sources

### 4.2 Runtime components

- FastAPI app for HTTP endpoints
- Local file loader for markdown ingestion
- Chunking logic that preserves metadata
- Embedding clients for Gemini and Ollama
- Chat clients for Gemini and Ollama
- Qdrant vector store wrapper
- RAG pipeline orchestrator
- Minimal HTML frontend
- Azure Container Apps deployment for API and Qdrant

## 5. Folder-by-Folder Explanation

### 5.1 `app/api`

This contains FastAPI route definitions.

- `health.py` exposes `/health`
- `query.py` exposes retrieval and answer endpoints
- `admin.py` exposes `/admin/reindex`

These files are intentionally thin. The routes translate HTTP requests into calls into the lower-level pipeline and indexing logic.

### 5.2 `app/core`

This contains project-wide configuration and provider selection.

- `config.py` loads environment variables into a `Settings` dataclass
- `providers.py` chooses Gemini or Ollama implementations based on environment settings

This is one of the most important design decisions in the project. Instead of scattering provider-specific logic throughout the app, the code centralizes that decision in one place.

### 5.3 `app/embeddings`

This folder contains embedding providers.

- `gemini_client.py`
- `ollama_client.py`

Both clients expose methods to embed a list of texts and to embed a query. Keeping a similar interface makes the rest of the code simpler.

### 5.4 `app/generation`

This folder contains answer generation logic.

- `prompts.py` builds the grounded prompt
- `gemini_chat.py` calls Gemini for answer generation
- `ollama_chat.py` calls Ollama for answer generation

The prompt builder is important because it shapes how the model behaves. It is where the retrieved context is turned into a model-readable instruction.

### 5.5 `app/ingestion`

This handles turning raw files into retrievable content.

- `local_files.py` loads markdown files
- `chunking.py` splits content into chunks
- `indexer.py` orchestrates the full reindex process

The indexing logic was factored into `indexer.py` so both the CLI script and the admin endpoint can reuse the same implementation.

### 5.6 `app/retrieval`

This folder contains the `RAGPipeline`.

The pipeline coordinates:

- embedding the question
- retrieving matching chunks from Qdrant
- building the prompt
- generating the final answer

This class is the center of the runtime query path.

### 5.7 `app/vectorstore`

This contains the Qdrant wrapper.

- `qdrant_store.py`

It hides the lower-level Qdrant client calls behind project-specific methods like collection recreation, upsert, and search.

### 5.8 `frontend`

This contains a tiny static HTML page used as the minimal frontend. It has:

- a text input
- an ask button
- an answer section
- a sources section

This is deliberately small so the frontend does not distract from the backend learning goals.

### 5.9 `scripts`

This contains operational and learning scripts.

- `index_chunks.py`
- `ask_rag.py`
- `search_chunks.py`

These are useful for testing the pipeline outside the API.

### 5.10 `tests`

This contains unit-ish and integration tests. Integration tests are explicitly marked so CI can skip them safely.

## 6. Key Files and Why They Matter

### 6.1 `app/core/config.py`

This file turns environment variables into a typed settings object. It matters because the whole application is configuration-driven:

- local versus azure environment
- Gemini versus Ollama
- Qdrant endpoint
- collection name
- admin key

Without a central settings object, deployment would become error-prone quickly.

### 6.2 `app/core/providers.py`

This file is the provider switchboard.

It answers:

- which embedding client should the app use
- which chat client should the app use

That means the rest of the code can ask for a chat client or embedding client without hardcoding Gemini or Ollama.

### 6.3 `app/retrieval/rag_pipeline.py`

This is the query-time orchestrator. It is where retrieval and generation meet.

Important responsibilities:

- create the right clients through the provider factory
- embed the incoming question
- fetch matching chunks
- build the final prompt
- return answer and sources

### 6.4 `app/ingestion/indexer.py`

This is the indexing-time orchestrator. It is where document ingestion and vector-store writes happen.

Important responsibilities:

- load raw docs
- chunk the docs
- generate embeddings
- recreate the collection
- upsert the points into Qdrant

### 6.5 `app/main.py`

This file wires the FastAPI app together.

It:

- creates the app instance
- includes routers
- serves the frontend at `/`

This file is small, which is good. App composition is centralized but not overloaded.

## 7. Request Lifecycle Walkthrough

This section explains exactly what happens when a user asks a question through the frontend or the API.

### 7.1 Frontend request

1. The user opens `/`.
2. The browser loads `frontend/index.html`.
3. The user types a question.
4. The page sends a request to `/query`.

### 7.2 API request

1. FastAPI receives `POST /query`.
2. The route in `app/api/query.py` validates the request body.
3. The route calls the `RAGPipeline`.

### 7.3 Retrieval step

1. The pipeline embeds the user question with the configured embedding provider.
2. The vector store searches Qdrant using that vector.
3. Matching chunks come back with metadata.

### 7.4 Generation step

1. The prompt builder combines the question with retrieved context.
2. The configured chat model receives the prompt.
3. The model returns an answer.
4. The API returns the answer plus sources to the client.

This clean separation between retrieval and generation is one of the best parts of the project because each half can be debugged separately.

## 8. Indexing Lifecycle Walkthrough

This section explains what happens when you run reindexing.

### 8.1 Entry points

There are two entry points:

- `python scripts/index_chunks.py`
- `POST /admin/reindex`

Both call into the shared indexing logic.

### 8.2 Loading documents

The loader reads markdown files from `data/raw`.

Each document typically includes:

- content body
- metadata such as title
- source path

### 8.3 Chunking

The content is split into chunks so retrieval can work at a smaller, more relevant granularity than full documents.

Chunking matters because:

- full documents are often too large and too noisy
- small chunks improve retrieval focus
- metadata can still be attached to each chunk

### 8.4 Embeddings

Each chunk is embedded through the active embedding provider.

For Gemini, the vector dimension observed in this project is `3072`.

### 8.5 Vector storage

The Qdrant collection is recreated and then the chunk vectors are upserted.

This gives you a clean fresh index, which is convenient during learning and early development.

## 9. Environment Variables Explained

### 9.1 General settings

- `APP_ENV`: local or azure style runtime context
- `LOG_LEVEL`: logging verbosity
- `ADMIN_API_KEY`: protects admin operations like reindex

### 9.2 Provider settings

- `LLM_PROVIDER`
- `EMBED_PROVIDER`

These let you choose Gemini or Ollama independently.

### 9.3 Gemini settings

- `GEMINI_API_KEY`
- `GEMINI_CHAT_MODEL`
- `GEMINI_EMBED_MODEL`

### 9.4 Ollama settings

- `OLLAMA_BASE_URL`
- `OLLAMA_CHAT_MODEL`
- `OLLAMA_EMBED_MODEL`

### 9.5 Qdrant settings

- `QDRANT_URL`
- `QDRANT_COLLECTION`

These are especially important because local and Azure deployments use different addressing.

## 10. Local Development Workflow

The usual local learning loop is:

1. start Qdrant
2. set `.env`
3. run indexing
4. run the API
5. ask questions through Swagger, the CLI script, or the frontend
6. run tests

Recommended commands:

```powershell
docker compose up -d qdrant
python scripts/index_chunks.py
uvicorn app.main:app --reload
pytest
```

## 11. Docker Workflow

The Docker image packages the API and the local knowledge base into one runnable container.

Important consequence:

When the image is built correctly, the `data/raw` files are inside the container image. This became very important during Azure debugging because it proved the cloud container already had the documents, even before indexing succeeded.

Useful commands:

```powershell
docker build -f docker/Dockerfile -t spark-ai-rag-assistant:local .
docker run --rm -p 8000:8000 --env-file .env spark-ai-rag-assistant:local
```

## 12. CI Workflow

The project uses GitHub Actions with a simple Python CI workflow.

The CI design intentionally excludes integration tests by marker:

```bash
pytest -m "not integration"
```

This matters because integration tests may require live services like Ollama or Qdrant, which are not always available in CI.

Benefits:

- faster CI
- more deterministic pipeline
- cleaner distinction between unit-ish and external-service tests

## 13. Azure Deployment Architecture

The Azure deployment uses:

- Azure Container Registry for images
- Azure Container Apps for the API
- Azure Container Apps for Qdrant
- Gemini API as the external model provider

### 13.1 API container

The API container runs the FastAPI app and serves:

- `/`
- `/docs`
- `/health`
- `/query`
- `/admin/reindex`

### 13.2 Qdrant container

Qdrant runs as a separate internal service container.

The API talks to it over the internal container app network.

### 13.3 Deployment flow

1. build the image locally
2. push it to ACR
3. update the Azure Container App to use that image
4. set environment variables and secrets
5. run indexing in the cloud or trigger reindex through the admin endpoint

## 14. Azure Issues Faced and What They Taught

This section is one of the most important learning sections in the document.

### 14.1 PowerShell multiline commands were written with `\`

Problem:

Unix-style line continuation was pasted into PowerShell.

Impact:

Commands failed with parse errors like:

- missing expression after unary operator `--`
- unexpected token `name`

Lesson:

PowerShell uses backticks for multiline commands, not backslashes.

### 14.2 `az containerapp up --source .` was unreliable here

Problem:

The high-level source-based deployment path tried to use Azure Cloud Build and failed with a managed environment builder error.

Lesson:

In this setup, the more reliable path was:

1. build Docker image
2. push to ACR
3. update Container App with explicit image tag

### 14.3 The app initially ran the Azure quickstart image

Problem:

The API app was not running the project image. It was still using the sample image `mcr.microsoft.com/k8se/quickstart:latest`.

Impact:

The configured target port and expected app behavior did not match the deployed container.

Lesson:

Always confirm the actual deployed image, not just the app name.

### 14.4 Main branch drift caused confusion

Problem:

The expected frontend and admin changes were not actually present on GitHub `main`.

Impact:

The cloud deployment could not show the frontend even though local code had it.

Lesson:

Always verify the actual remote branch head and tree before assuming the deploy target is current.

### 14.5 Gemini was not the issue once embeddings succeeded

Problem:

The project originally failed in multiple places while introducing Gemini.

Observation:

Once the Azure-hosted API successfully generated embeddings, Gemini configuration was proven good enough for the embedding path.

Lesson:

When debugging a pipeline, identify the last successful stage. In this case, the breakage was after embeddings, not before.

### 14.6 Qdrant connectivity was the hardest deployment issue

Problem:

The API container repeatedly timed out while talking to Qdrant.

Final working setup:

- Qdrant kept as a separate Azure Container App
- internal TCP ingress used on port `6333`
- Qdrant forced to bind to `0.0.0.0`
- API pointed to `http://spark-ai-qdrant:6333`
- minimum replica kept warm

Lesson:

A service can look healthy in Azure and still be unreachable from another container if ingress mode and listener configuration do not match the protocol.

### 14.7 Running indexing inside the container was useful, but not ideal

Problem:

Manual shelling into the API container to run indexing was operationally awkward.

Lesson:

The protected `/admin/reindex` endpoint is a better operational tool for routine reindexing.

## 15. Security and Operational Considerations

Important areas to think about:

- secrets should be stored in environment secrets, not hardcoded
- admin operations should be protected
- deployed containers should use the correct image tag
- Qdrant persistence should be planned if the dataset matters long term
- logs should be reviewed during deployment changes

One practical learning from this project is that leaked API keys and registry passwords should be rotated immediately after exposure.

## 16. Testing Strategy

The testing strategy is intentionally simple.

### 16.1 Unit-ish tests

These cover:

- health endpoint behavior
- local loading
- chunking
- prompt building
- frontend route behavior
- admin route behavior

### 16.2 Integration tests

These cover service-dependent flows like:

- query API against real providers
- RAG pipeline against real services

The `integration` marker makes these tests easy to separate.

## 17. Why the Tiny Frontend Exists

The frontend is not meant to be a production UI. It exists to make the project easier to demo and learn from.

It is valuable because:

- it proves the backend is usable by a browser client
- it provides a simple end-to-end test surface
- it avoids the overhead of a full frontend framework

This is a good example of matching the implementation to the learning goal.

## 18. How to Extend the Project

Here are sensible next steps.

### 18.1 Better indexing sources

Add:

- Confluence API ingestion
- GitHub docs ingestion
- blob storage ingestion

### 18.2 Better operations

Add:

- persistent Qdrant storage
- scheduled reindex jobs
- richer admin authentication
- structured logging
- monitoring dashboards

### 18.3 Better retrieval

Add:

- hybrid search
- metadata filtering
- reranking
- chunk overlap tuning
- answer confidence handling

### 18.4 Better frontend

Add:

- loading state
- source links
- conversation history
- copy answer button

## 19. End-to-End Mental Model

If you want one compact way to remember the whole project, use this:

This project has two big loops.

Indexing loop:

documents -> chunks -> embeddings -> Qdrant

Answering loop:

question -> query embedding -> Qdrant retrieval -> prompt -> LLM answer

And it has three operating surfaces:

- scripts for direct learning and debugging
- FastAPI for application access
- Azure deployment for cloud usage

That mental model is enough to re-derive most of the code structure later.

## 20. Final Summary

This project is a good learning example because it covers several important engineering skills at once:

- backend API design
- RAG architecture
- prompt assembly
- vector database usage
- provider abstraction without overengineering
- CI hygiene
- Docker packaging
- cloud deployment troubleshooting

The most valuable lesson is that a working AI application is not just model code. It is the combination of ingestion, retrieval, API design, deployment, configuration, operational debugging, and disciplined testing.

If you keep this document alongside the README, you should have both:

- a concise project overview
- a detailed learning reference
