"""Tests for Alembic database migrations."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _alembic_config(database_url: str) -> Config:
    """Create an Alembic configuration for a test database."""
    backend_dir = Path(__file__).resolve().parents[2]

    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        database_url,
    )

    return config


def test_upgrade_to_head_creates_domain_schema(
    tmp_path: Path,
) -> None:
    """Upgrading to head must create all expected tables."""
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"

    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)

        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert {
            "alembic_version",
            "devices",
            "sync_states",
            "users",
            "employments",
            "customers",
            "projects",
            "project_assignments",
        } <= tables

    finally:
        engine.dispose()


def test_downgrade_from_head_removes_domain_schema(
    tmp_path: Path,
) -> None:
    """Downgrading from head must remove Sprint-B domain tables."""
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"

    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)

        command.upgrade(config, "head")
        command.downgrade(config, "0001_initial_schema")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert "users" not in tables
        assert "employments" not in tables
        assert "customers" not in tables
        assert "projects" not in tables
        assert "project_assignments" not in tables

        assert "devices" in tables
        assert "sync_states" in tables

    finally:
        engine.dispose()
