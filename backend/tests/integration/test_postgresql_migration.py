"""PostgreSQL integration tests for the Alembic migration workflow."""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.models import (
    Customer,
    CustomerType,
    Employment,
    ExternalRelationship,
    ExternalRelationshipType,
    Project,
    ProjectAssignment,
    User,
    UserRole,
    UserType,
)
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG_PATH = BACKEND_ROOT / "alembic.ini"


def _database_url() -> str:
    """Return the PostgreSQL test database URL or skip the test."""
    database_url = os.getenv("GLASHAUS_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GLASHAUS_TEST_DATABASE_URL is not configured")
    return database_url


def _alembic_config(database_url: str) -> Config:
    """Build an Alembic configuration for the test database."""
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_postgresql_migration_reaches_head() -> None:
    """The complete migration chain must reach the current head."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)

        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "devices",
            "sync_states",
            "users",
            "employments",
            "customers",
            "projects",
            "project_assignments",
            "external_relationships",
        }
    finally:
        engine.dispose()


def test_postgresql_domain_roundtrip() -> None:
    """The core domain graph must persist and reload on PostgreSQL."""
    database_url = _database_url()
    engine = create_engine(database_url)

    try:
        config = _alembic_config(database_url)
        command.upgrade(config, "head")

        with Session(engine) as session:
            user = User(
                login_identifier="postgres-roundtrip-user",
                display_name="PostgreSQL Roundtrip User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            customer = Customer(
                name="PostgreSQL Test Customer",
                customer_type=CustomerType.COMPANY,
            )
            session.add_all([user, customer])
            session.flush()

            employment = Employment(
                user_id=user.id,
                hierarchy_level="LEVEL_1",
                employment_status="ACTIVE",
                valid_from=user.created_at,
            )
            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Test Project",
                status="ACTIVE",
            )
            session.add_all([employment, project])
            session.flush()

            assignment = ProjectAssignment(
                user_id=user.id,
                project_id=project.id,
                assignment_context="PostgreSQL roundtrip",
                valid_from=project.created_at,
            )
            session.add(assignment)
            session.commit()

            persisted_user_id = user.id
            persisted_customer_id = customer.id
            persisted_project_id = project.id
            persisted_assignment_id = assignment.id

        with Session(engine) as session:
            loaded_user = session.get(User, persisted_user_id)
            loaded_customer = session.get(Customer, persisted_customer_id)
            loaded_project = session.get(Project, persisted_project_id)
            loaded_assignment = session.get(
                ProjectAssignment,
                persisted_assignment_id,
            )

            assert loaded_user is not None
            assert loaded_user.login_identifier == "postgres-roundtrip-user"
            assert loaded_user.display_name == "PostgreSQL Roundtrip User"
            assert loaded_user.user_type is UserType.INTERNAL
            assert loaded_user.role is UserRole.TECHNICIAN

            assert loaded_customer is not None
            assert loaded_customer.customer_type is CustomerType.COMPANY

            assert loaded_project is not None
            assert loaded_project.customer_id == persisted_customer_id

            assert loaded_assignment is not None
            assert loaded_assignment.user_id == persisted_user_id
            assert loaded_assignment.project_id == persisted_project_id
    finally:
        engine.dispose()


def test_postgresql_migration_can_downgrade() -> None:
    """The PostgreSQL database must be able to downgrade to base."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    try:
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()


def test_postgresql_external_relationship_schema() -> None:
    """PostgreSQL must create the external relationship schema correctly."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column
            for column in inspector.get_columns("external_relationships")
        }

        assert "created_from" in columns
        assert columns["created_from"]["nullable"] is False

        foreign_keys = inspector.get_foreign_keys(
            "external_relationships",
        )

        created_from_foreign_key = next(
            foreign_key
            for foreign_key in foreign_keys
            if foreign_key["constrained_columns"] == ["created_from"]
        )

        assert created_from_foreign_key["referred_table"] == "users"
        assert created_from_foreign_key["referred_columns"] == ["id"]
        assert created_from_foreign_key["options"]["ondelete"] == "RESTRICT"
    finally:
        engine.dispose()


def test_postgresql_external_relationship_uses_timezone_aware_timestamps() -> None:
    """ExternalRelationship timestamps must use PostgreSQL TIMESTAMP WITH TIME ZONE."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column
            for column in inspector.get_columns("external_relationships")
        }

        for column_name in (
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        ):
            column_type = columns[column_name]["type"]

            assert isinstance(column_type, TIMESTAMP)
            assert column_type.timezone is True
    finally:
        engine.dispose()


def test_postgresql_external_relationship_utc_roundtrip() -> None:
    """UTC-aware relationship timestamps must survive a PostgreSQL roundtrip."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    valid_from = datetime(
        2026,
        1,
        1,
        12,
        30,
        tzinfo=UTC,
    )
    valid_until = datetime(
        2026,
        12,
        31,
        18,
        45,
        tzinfo=UTC,
    )

    try:
        with Session(engine) as session:
            user = User(
                login_identifier="postgres-external-relationship-user",
                display_name="PostgreSQL External Relationship User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            customer = Customer(
                name="PostgreSQL External Relationship Customer",
                customer_type=CustomerType.COMPANY,
            )

            session.add_all([user, customer])
            session.flush()

            relationship = ExternalRelationship(
                user_id=user.id,
                customer_id=customer.id,
                relationship_type=ExternalRelationshipType.OWNER,
                valid_from=valid_from,
                valid_until=valid_until,
                active=True,
                created_from=user.id,
            )

            session.add(relationship)
            session.commit()

            relationship_id = relationship.id

        with Session(engine) as session:
            loaded = session.get(
                ExternalRelationship,
                relationship_id,
            )

            assert loaded is not None
            assert loaded.valid_from == valid_from
            assert loaded.valid_from.tzinfo is not None

            assert loaded.valid_until == valid_until
            assert loaded.valid_until.tzinfo is not None

            assert loaded.created_at.tzinfo is not None
            assert loaded.updated_at.tzinfo is not None
    finally:
        engine.dispose()
