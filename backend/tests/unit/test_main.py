"""Unit tests for the main GlasHaus backend application."""

from app.main import app
from fastapi.testclient import TestClient


def test_health_check() -> None:
    """Verify that the backend health endpoint is available."""
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "GlasHaus backend running"}
