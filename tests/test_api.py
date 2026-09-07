"""
API integration tests.

Uses FastAPI's TestClient — no live server required.
"""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """GET /health should return 200 with status 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
