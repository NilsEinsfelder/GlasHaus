"""Unit tests for the main GlasHaus backend application."""

from app.main import app
from fastapi.testclient import TestClient


def test_root_health_check() -> None:
    """Verify that the root health endpoint is available."""
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "GlasHaus backend running"}


def test_health_status() -> None:
    """Verify that the dedicated health endpoint is available."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
