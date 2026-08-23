"""Unit tests for application configuration."""

from app.core.config import Settings


def test_default_settings_use_development_sqlite() -> None:
    """Development settings must provide a local SQLite default."""
    settings = Settings()

    assert settings.environment == "development"
    assert settings.database_url == "sqlite:///./glashaus.db"
    assert settings.sql_echo is False
