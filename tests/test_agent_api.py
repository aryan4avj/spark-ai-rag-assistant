from fastapi.testclient import TestClient

from app.api import agent as agent_api
from app.main import app
from tests.test_agent_graph import FakePipeline, make_chunk

client = TestClient(app)


def test_agent_query_endpoint_returns_agent_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        agent_api,
        "agent",
        agent_api.SparkAgent(pipeline=FakePipeline(chunks=[make_chunk()])),
    )

    response = client.post(
        "/agent/query",
        json={
            "question": "How does RAG reduce hallucination?",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How does RAG reduce hallucination?"
    assert data["route"] == "rag"
    assert data["tool_name"] == "doc_lookup_tool"
    assert data["answer"]
    assert data["sources"][0]["chunk_id"] == "chunk-1"
    assert "retrieve_documents" in data["timing_ms"]
