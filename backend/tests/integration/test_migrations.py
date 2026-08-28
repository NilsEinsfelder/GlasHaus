"""Integration tests for the Alembic migration workflow."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

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
    "permissions",
    "permission_grants",
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
        inspector = inspect(engine)

        assert set(inspector.get_table_names()) == FULL_SCHEMA_TABLES

        columns = {
            column["name"]: column
            for column in inspector.get_columns("permission_grants")
        }

        assert set(columns) == {
            "id",
            "user_id",
            "permission_id",
            "effect",
            "scope_type",
            "scope_id",
            "constraint_type",
            "constraint_value",
            "valid_from",
            "valid_until",
            "active",
            "granted_by_user_id",
            "created_at",
            "updated_at",
        }

        assert columns["constraint_value"]["nullable"] is True

        foreign_keys = inspector.get_foreign_keys("permission_grants")
        foreign_key_map = {
            tuple(foreign_key["constrained_columns"]): foreign_key
            for foreign_key in foreign_keys
        }

        assert foreign_key_map[("user_id",)]["referred_table"] == "users"
        assert foreign_key_map[("permission_id",)]["referred_table"] == "permissions"
        assert foreign_key_map[("granted_by_user_id",)]["referred_table"] == "users"

        indexes = inspector.get_indexes("permission_grants")
        index_names = {index["name"] for index in indexes}

        assert {
            "ix_permission_grants_user_id",
            "ix_permission_grants_permission_id",
            "ix_permission_grants_granted_by_user_id",
            "ix_permission_grants_user_permission_active",
            "ix_permission_grants_scope_active",
        }.issubset(index_names)
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


def test_permission_grant_migration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The PermissionGrant migration creates the documented schema."""
    database_url = f"sqlite:///{tmp_path / 'permission-grant-migration-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.core.config import get_settings

    get_settings.cache_clear()

    config = Config(str(ALEMBIC_CONFIG_PATH))

    command.upgrade(config, "0006_permission")

    engine = create_engine(database_url)

    try:
        assert "permissions" in inspect(engine).get_table_names()
        assert "permission_grants" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "0007_permission_grant")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        assert "permission_grants" in inspector.get_table_names()

        columns = {
            column["name"]: column
            for column in inspector.get_columns("permission_grants")
        }

        assert set(columns) == {
            "id",
            "user_id",
            "permission_id",
            "effect",
            "scope_type",
            "scope_id",
            "constraint_type",
            "constraint_value",
            "valid_from",
            "valid_until",
            "active",
            "granted_by_user_id",
            "created_at",
            "updated_at",
        }

        assert columns["id"]["nullable"] is False
        assert columns["user_id"]["nullable"] is False
        assert columns["permission_id"]["nullable"] is False
        assert columns["effect"]["nullable"] is False
        assert columns["scope_type"]["nullable"] is False
        assert columns["scope_id"]["nullable"] is True
        assert columns["constraint_type"]["nullable"] is True
        assert columns["constraint_value"]["nullable"] is True
        assert columns["valid_from"]["nullable"] is False
        assert columns["valid_until"]["nullable"] is True
        assert columns["active"]["nullable"] is False
        assert columns["granted_by_user_id"]["nullable"] is False

        foreign_keys = inspector.get_foreign_keys(
            "permission_grants",
        )

        foreign_key_map = {
            tuple(foreign_key["constrained_columns"]): foreign_key
            for foreign_key in foreign_keys
        }

        assert foreign_key_map[("user_id",)]["referred_table"] == "users"
        assert foreign_key_map[("user_id",)]["options"]["ondelete"] == "RESTRICT"

        assert foreign_key_map[("permission_id",)]["referred_table"] == "permissions"
        assert foreign_key_map[("permission_id",)]["options"]["ondelete"] == "RESTRICT"

        assert foreign_key_map[("granted_by_user_id",)]["referred_table"] == "users"
        assert (
            foreign_key_map[("granted_by_user_id",)]["options"]["ondelete"]
            == "RESTRICT"
        )

        indexes = inspector.get_indexes("permission_grants")
        index_names = {index["name"] for index in indexes}

        assert {
            "ix_permission_grants_user_id",
            "ix_permission_grants_permission_id",
            "ix_permission_grants_granted_by_user_id",
            "ix_permission_grants_user_permission_active",
            "ix_permission_grants_scope_active",
        }.issubset(index_names)

        check_constraints = inspector.get_check_constraints(
            "permission_grants",
        )
        check_constraint_names = {
            constraint["name"] for constraint in check_constraints
        }

        assert check_constraint_names == {
            "ck_permission_grants_effect",
            "ck_permission_grants_scope_type",
            "ck_permission_grants_scope_consistency",
            "ck_permission_grants_valid_range",
            "ck_permission_grants_constraint_consistency",
        }
    finally:
        engine.dispose()

    command.downgrade(config, "0006_permission")

    engine = create_engine(database_url)

    try:
        assert "permission_grants" not in inspect(engine).get_table_names()
        assert "permissions" in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    get_settings.cache_clear()


def test_permission_grant_migration_preserves_json_constraint_semantics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The migrated SQLite schema supports generic JSON constraints."""
    database_url = f"sqlite:///{tmp_path / 'permission-grant.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.core.config import get_settings

    get_settings.cache_clear()

    config = Config(str(ALEMBIC_CONFIG_PATH))
    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                """
                INSERT INTO users (
                    id,
                    login_identifier,
                    display_name,
                    user_type,
                    role,
                    active,
                    created_at,
                    updated_at
                )
                VALUES (
                    '11111111-1111-7111-8111-111111111111',
                    'migration-grant-user',
                    'Migration Grant User',
                    'INTERNAL',
                    'TECHNICIAN',
                    1,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO users (
                    id,
                    login_identifier,
                    display_name,
                    user_type,
                    role,
                    active,
                    created_at,
                    updated_at
                )
                VALUES (
                    '22222222-2222-7222-8222-222222222222',
                    'migration-grant-grantor',
                    'Migration Grant Grantor',
                    'INTERNAL',
                    'TECHNICIAN',
                    1,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO permissions (id, identifier)
                VALUES (
                    '33333333-3333-7333-8333-333333333333',
                    'migration.purchase.create'
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO permission_grants (
                    id,
                    user_id,
                    permission_id,
                    effect,
                    scope_type,
                    scope_id,
                    constraint_type,
                    constraint_value,
                    valid_from,
                    active,
                    granted_by_user_id,
                    created_at,
                    updated_at
                )
                VALUES (
                    '44444444-4444-7444-8444-444444444444',
                    '11111111-1111-7111-8111-111111111111',
                    '33333333-3333-7333-8333-333333333333',
                    'ALLOW',
                    'PROJECT',
                    '55555555-5555-7555-8555-555555555555',
                    'purchase_limit',
                    '{"amount":"2000.50","currency":"EUR"}',
                    CURRENT_TIMESTAMP,
                    1,
                    '22222222-2222-7222-8222-222222222222',
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO permission_grants (
                    id,
                    user_id,
                    permission_id,
                    effect,
                    scope_type,
                    scope_id,
                    constraint_type,
                    constraint_value,
                    valid_from,
                    active,
                    granted_by_user_id,
                    created_at,
                    updated_at
                )
                VALUES (
                    '66666666-6666-7666-8666-666666666666',
                    '11111111-1111-7111-8111-111111111111',
                    '33333333-3333-7333-8333-333333333333',
                    'ALLOW',
                    'GLOBAL',
                    NULL,
                    'purchase_limit',
                    NULL,
                    CURRENT_TIMESTAMP,
                    1,
                    '22222222-2222-7222-8222-222222222222',
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

        with engine.connect() as connection:
            rows = connection.exec_driver_sql(
                """
                SELECT
                    scope_type,
                    constraint_type,
                    constraint_value
                FROM permission_grants
                ORDER BY id
                """
            ).all()

        assert rows == [
            (
                "PROJECT",
                "purchase_limit",
                '{"amount":"2000.50","currency":"EUR"}',
            ),
            (
                "GLOBAL",
                "purchase_limit",
                None,
            ),
        ]
    finally:
        engine.dispose()

        get_settings.cache_clear()


def test_permission_grant_migration_rejects_constraint_value_without_type(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A constraint value without a constraint type must be rejected."""
    database_url = f"sqlite:///{tmp_path / 'permission-grant-invalid.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.core.config import get_settings

    get_settings.cache_clear()

    config = Config(str(ALEMBIC_CONFIG_PATH))
    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                """
                INSERT INTO users (
                    id,
                    login_identifier,
                    display_name,
                    user_type,
                    role,
                    active,
                    created_at,
                    updated_at
                )
                VALUES (
                    '11111111-1111-7111-8111-111111111111',
                    'invalid-grant-user',
                    'Invalid Grant User',
                    'INTERNAL',
                    'TECHNICIAN',
                    1,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO users (
                    id,
                    login_identifier,
                    display_name,
                    user_type,
                    role,
                    active,
                    created_at,
                    updated_at
                )
                VALUES (
                    '22222222-2222-7222-8222-222222222222',
                    'invalid-grant-grantor',
                    'Invalid Grant Grantor',
                    'INTERNAL',
                    'TECHNICIAN',
                    1,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )

            connection.exec_driver_sql(
                """
                INSERT INTO permissions (id, identifier)
                VALUES (
                    '33333333-3333-7333-8333-333333333333',
                    'migration.invalid.constraint'
                )
                """
            )

            with pytest.raises(IntegrityError):
                connection.exec_driver_sql(
                    """
                    INSERT INTO permission_grants (
                        id,
                        user_id,
                        permission_id,
                        effect,
                        scope_type,
                        scope_id,
                        constraint_type,
                        constraint_value,
                        valid_from,
                        active,
                        granted_by_user_id,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        '44444444-4444-7444-8444-444444444444',
                        '11111111-1111-7111-8111-111111111111',
                        '33333333-3333-7333-8333-333333333333',
                        'ALLOW',
                        'GLOBAL',
                        NULL,
                        NULL,
                        '{"unexpected":true}',
                        CURRENT_TIMESTAMP,
                        1,
                        '22222222-2222-7222-8222-222222222222',
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                    """
                )
    finally:
        engine.dispose()

        get_settings.cache_clear()
