import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def test_retrieve_endpoint_returns_chunks() -> None:
    response = client.post(
        "/retrieve",
        json={
            "question": "How does RAG reduce hallucination?",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How does RAG reduce hallucination?"
    assert len(data["chunks"]) > 0
    assert "title" in data["chunks"][0]
    assert "content" in data["chunks"][0]
    assert "source_number" in data["chunks"][0]


def test_query_endpoint_returns_answer_and_sources() -> None:
    response = client.post(
        "/query",
        json={
            "question": "How does RAG reduce hallucination?",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How does RAG reduce hallucination?"
    assert data["answer"]
    assert len(data["sources"]) > 0
    assert "title" in data["sources"][0]
    assert "source_number" in data["sources"][0]
