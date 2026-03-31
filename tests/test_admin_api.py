from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_reindex_requires_configured_admin_key(monkeypatch) -> None:
    monkeypatch.setattr("app.api.admin.settings.admin_api_key", "")

    response = client.post("/admin/reindex")

    assert response.status_code == 503
    assert response.json()["detail"] == "ADMIN_API_KEY is not configured."


def test_reindex_rejects_invalid_admin_key(monkeypatch) -> None:
    monkeypatch.setattr("app.api.admin.settings.admin_api_key", "expected-key")

    response = client.post(
        "/admin/reindex",
        headers={"x-admin-api-key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid admin API key."


def test_reindex_returns_counts_when_authorized(monkeypatch) -> None:
    monkeypatch.setattr("app.api.admin.settings.admin_api_key", "expected-key")

    class FakeResult:
        document_count = 3
        chunk_count = 9
        vector_size = 3072

    monkeypatch.setattr("app.api.admin.reindex_documents", lambda: FakeResult())

    response = client.post(
        "/admin/reindex",
        headers={"x-admin-api-key": "expected-key"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "documents_indexed": 3,
        "chunks_indexed": 9,
        "vector_size": 3072,
    }
