from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_frontend() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Spark AI" in response.text
