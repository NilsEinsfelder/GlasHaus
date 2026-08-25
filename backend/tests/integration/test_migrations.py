"""Integration tests for the Alembic migration workflow."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG_PATH = BACKEND_ROOT / "alembic.ini"


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

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "devices",
            "sync_states",
        }
    finally:
        engine.dispose()

    command.downgrade(config, "base")

    engine = create_engine(database_url)

    try:
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "devices",
            "sync_states",
        }
    finally:
        engine.dispose()

    get_settings.cache_clear()
