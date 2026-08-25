"""Unit tests for application configuration."""

import pytest
from app.core.config import Settings
from pydantic import ValidationError
from pytest import MonkeyPatch


def test_default_settings_use_development_sqlite(
    monkeypatch: MonkeyPatch,
) -> None:
    """Development settings must provide local default values."""
    for variable in (
        "APP_NAME",
        "ENVIRONMENT",
        "DATABASE_URL",
        "SQL_ECHO",
        "LOG_LEVEL",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.database_url == "sqlite:///./glashaus.db"
    assert settings.sql_echo is False
    assert settings.log_level == "INFO"


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
