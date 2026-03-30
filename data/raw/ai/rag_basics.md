---
doc_id: ai-001
title: RAG Basics
source: internal_wiki
space: AI
author: Aryan Vikas Jain
created_at: 2026-03-30
updated_at: 2026-03-30
tags: [rag, llm, retrieval]
url: https://internal.example.com/ai/rag-basics
---

# RAG Basics

Retrieval-Augmented Generation, or RAG, is a pattern where a language model is provided with external context retrieved from a knowledge source before answering a user query.

## Why RAG is useful

RAG reduces hallucination risk by grounding the answer in retrieved context. It also allows teams to use private knowledge bases without retraining the model.

## Common RAG pipeline

A typical pipeline includes document ingestion, text cleaning, chunking, embedding generation, vector storage, retrieval, context assembly, and answer generation.

## Common failure modes

Failure modes include bad chunking, poor retrieval, irrelevant context, stale data, and weak prompt instructions.
