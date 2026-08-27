"""Integration tests for the Alembic migration workflow."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG_PATH = BACKEND_ROOT / "alembic.ini"

INITIAL_SCHEMA_TABLES = {
    "alembic_version",
    "devices",
    "sync_states",
}

FULL_SCHEMA_TABLES = {
    "alembic_version",
    "devices",
    "sync_states",
    "users",
    "employments",
    "customers",
    "projects",
    "project_assignments",
    "external_relationships",
    "customer_project_accesses",
    "workspaces",
}


def test_alembic_upgrade_and_downgrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The complete migration cycle must work on an isolated SQLite database."""
    database_url = f"sqlite:///{tmp_path / 'migration-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.core.config import get_settings

    get_settings.cache_clear()

    config = Config(str(ALEMBIC_CONFIG_PATH))

    # base -> head: the complete schema must be created.
    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        assert set(inspect(engine).get_table_names()) == FULL_SCHEMA_TABLES
    finally:
        engine.dispose()

    # head -> base: Alembic's version table remains, while all
    # application tables are removed.
    command.downgrade(config, "base")

    engine = create_engine(database_url)

    try:
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()

    # base -> 0001: only the initial infrastructure schema must exist.
    command.upgrade(config, "0001_initial_schema")

    engine = create_engine(database_url)

    try:
        assert set(inspect(engine).get_table_names()) == INITIAL_SCHEMA_TABLES
    finally:
        engine.dispose()

    # 0001 -> head: the domain migration must restore the complete schema.
    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        assert set(inspect(engine).get_table_names()) == FULL_SCHEMA_TABLES
    finally:
        engine.dispose()

    get_settings.cache_clear()
