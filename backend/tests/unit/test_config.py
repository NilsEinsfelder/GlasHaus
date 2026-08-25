"""Unit tests for application configuration."""

import pytest
from app.core.config import Settings
from pydantic import ValidationError


def test_default_settings_use_development_sqlite(
    monkeypatch,
) -> None:
    """Development settings must provide a local SQLite default."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    settings = Settings()

    assert settings.environment == "development"
    assert settings.database_url == "sqlite:///./glashaus.db"


def test_production_settings_accept_postgresql() -> None:
    """Production settings must accept PostgreSQL URLs."""
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://user:password@localhost/glashaus",
    )

    assert settings.environment == "production"
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_production_settings_accept_standard_postgresql_scheme() -> None:
    """Production settings must accept the standard PostgreSQL scheme."""
    settings = Settings(
        environment="production",
        database_url="postgresql://user:password@localhost/glashaus",
    )

    assert settings.environment == "production"


def test_production_settings_reject_sqlite() -> None:
    """Production settings must reject SQLite."""
    with pytest.raises(
        ValidationError,
        match="Production environment requires a PostgreSQL database URL",
    ):
        Settings(
            environment="production",
            database_url="sqlite:///./glashaus.db",
        )
