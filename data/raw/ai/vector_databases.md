---
doc_id: ai-003
title: Vector Databases
source: internal_wiki
space: AI
author: Aryan Vikas Jain
created_at: 2026-03-30
updated_at: 2026-03-30
tags: [vector-db, qdrant, retrieval]
url: https://internal.example.com/ai/vector-databases
---

# Vector Databases

A vector database stores embeddings and allows nearest-neighbor similarity search over them.

## What is stored

A vector database usually stores a vector, an ID, and metadata payload. Metadata is important for filtering, tracing, and citation.

## Why metadata filtering matters

Semantic similarity alone is not always enough. Metadata filters can restrict results by team, space, time, or document type.
