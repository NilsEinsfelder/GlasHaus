"""Unit tests for the main GlasHaus backend application."""

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.main import create_app
from fastapi.testclient import TestClient


def test_root_health_check() -> None:
    """Verify that the root health endpoint is available."""
    app = create_app(Settings())

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "GlasHaus backend running"}


def test_health_status() -> None:
    """Verify that the dedicated health endpoint is available."""
    app = create_app(Settings())

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_application_error_returns_controlled_response() -> None:
    """Expected application failures must return their public error contract."""
    app = create_app(Settings())

    @app.get("/test/application-error")
    def application_error_route() -> None:
        raise ApplicationError(
            "The requested resource is unavailable.",
            status_code=409,
            code="resource_unavailable",
        )

    with TestClient(app) as client:
        response = client.get("/test/application-error")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "The requested resource is unavailable.",
        "code": "resource_unavailable",
    }


def test_unexpected_error_does_not_leak_internal_details() -> None:
    """Unexpected failures must return a generic error response."""
    app = create_app(Settings())

    @app.get("/test/unexpected-error")
    def unexpected_error_route() -> None:
        raise RuntimeError("super-secret database password")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test/unexpected-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "code": "internal_server_error",
    }
