"""PostgreSQL integration tests for the Alembic migration workflow."""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.models import (
    Customer,
    CustomerProjectAccess,
    CustomerType,
    Employment,
    ExternalRelationship,
    ExternalRelationshipType,
    Permission,
    PermissionGrant,
    PermissionGrantConstraintType,
    PermissionGrantEffect,
    PermissionGrantScopeType,
    Project,
    ProjectAssignment,
    User,
    UserRole,
    UserType,
    Workspace,
    WorkspaceType,
)
from sqlalchemy import create_engine, inspect, select
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
            "customer_project_accesses",
            "workspaces",
            "permissions",
            "permission_grants",
            "permission_grant_constraints",
            "permission_grant_effects",
            "permission_grant_scopes",
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


def test_postgresql_customer_project_access_schema() -> None:
    """PostgreSQL must create the customer project access schema correctly."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column
            for column in inspector.get_columns("customer_project_accesses")
        }

        assert set(columns) == {
            "id",
            "project_id",
            "user_id",
            "valid_from",
            "valid_until",
            "active",
            "created_from",
            "created_at",
            "updated_at",
        }

        assert columns["id"]["nullable"] is False
        assert columns["project_id"]["nullable"] is False
        assert columns["user_id"]["nullable"] is False
        assert columns["valid_from"]["nullable"] is False
        assert columns["valid_until"]["nullable"] is True
        assert columns["active"]["nullable"] is False
        assert columns["created_from"]["nullable"] is False

        foreign_keys = inspector.get_foreign_keys(
            "customer_project_accesses",
        )

        foreign_key_map = {
            tuple(foreign_key["constrained_columns"]): foreign_key
            for foreign_key in foreign_keys
        }

        project_foreign_key = foreign_key_map[("project_id",)]
        assert project_foreign_key["referred_table"] == "projects"
        assert project_foreign_key["referred_columns"] == ["id"]
        assert project_foreign_key["options"]["ondelete"] == "RESTRICT"

        user_foreign_key = foreign_key_map[("user_id",)]
        assert user_foreign_key["referred_table"] == "users"
        assert user_foreign_key["referred_columns"] == ["id"]
        assert user_foreign_key["options"]["ondelete"] == "RESTRICT"

        created_from_foreign_key = foreign_key_map[("created_from",)]
        assert created_from_foreign_key["referred_table"] == "users"
        assert created_from_foreign_key["referred_columns"] == ["id"]
        assert created_from_foreign_key["options"]["ondelete"] == "RESTRICT"
    finally:
        engine.dispose()


def test_postgresql_workspace_schema() -> None:
    """PostgreSQL must create the workspace schema correctly."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column for column in inspector.get_columns("workspaces")
        }

        assert set(columns) == {
            "id",
            "project_id",
            "workspace_type",
            "created_from",
            "created_at",
            "updated_at",
        }

        assert columns["id"]["nullable"] is False
        assert columns["project_id"]["nullable"] is False
        assert columns["workspace_type"]["nullable"] is False
        assert columns["created_from"]["nullable"] is False
        assert columns["created_at"]["nullable"] is False
        assert columns["updated_at"]["nullable"] is False

        foreign_keys = inspector.get_foreign_keys("workspaces")

        foreign_key_map = {
            tuple(foreign_key["constrained_columns"]): foreign_key
            for foreign_key in foreign_keys
        }

        project_foreign_key = foreign_key_map[("project_id",)]
        assert project_foreign_key["referred_table"] == "projects"
        assert project_foreign_key["referred_columns"] == ["id"]
        assert project_foreign_key["options"]["ondelete"] == "RESTRICT"

        created_from_foreign_key = foreign_key_map[("created_from",)]
        assert created_from_foreign_key["referred_table"] == "users"
        assert created_from_foreign_key["referred_columns"] == ["id"]
        assert created_from_foreign_key["options"]["ondelete"] == "RESTRICT"
    finally:
        engine.dispose()


def test_postgresql_customer_project_access_uses_timezone_aware_timestamps() -> None:
    """CustomerProjectAccess timestamps must use PostgreSQL TIMESTAMP WITH TIME ZONE."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column
            for column in inspector.get_columns("customer_project_accesses")
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


def test_postgresql_workspace_uses_timezone_aware_timestamps() -> None:
    """Workspace timestamps must use PostgreSQL TIMESTAMP WITH TIME ZONE."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column for column in inspector.get_columns("workspaces")
        }

        for column_name in (
            "created_at",
            "updated_at",
        ):
            column_type = columns[column_name]["type"]

            assert isinstance(column_type, TIMESTAMP)
            assert column_type.timezone is True
    finally:
        engine.dispose()


def test_postgresql_customer_project_access_utc_roundtrip() -> None:
    """Customer project access must persist the complete external customer access chain."""
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
            internal_user = User(
                login_identifier="postgres-customer-access-internal-user",
                display_name="PostgreSQL Customer Access Internal User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            external_user = User(
                login_identifier="postgres-customer-access-external-user",
                display_name="PostgreSQL Customer Access External User",
                user_type=UserType.EXTERNAL,
                role=UserRole.CUSTOMER,
            )
            customer = Customer(
                name="PostgreSQL Customer Access Customer",
                customer_type=CustomerType.COMPANY,
            )

            session.add_all(
                [
                    internal_user,
                    external_user,
                    customer,
                ]
            )
            session.flush()

            relationship = ExternalRelationship(
                user_id=external_user.id,
                customer_id=customer.id,
                relationship_type=ExternalRelationshipType.OWNER,
                valid_from=valid_from,
                active=True,
                created_from=internal_user.id,
            )
            session.add(relationship)
            session.flush()

            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Customer Access Project",
                status="ACTIVE",
            )
            session.add(project)
            session.flush()

            access = CustomerProjectAccess(
                project_id=project.id,
                user_id=external_user.id,
                valid_from=valid_from,
                valid_until=valid_until,
                active=True,
                created_from=internal_user.id,
            )
            session.add(access)
            session.flush()

            internal_user_id = internal_user.id
            external_user_id = external_user.id
            customer_id = customer.id
            relationship_id = relationship.id
            project_id = project.id
            access_id = access.id

            session.commit()

        with Session(engine) as session:
            loaded_relationship = session.get(
                ExternalRelationship,
                relationship_id,
            )
            loaded_project = session.get(
                Project,
                project_id,
            )
            loaded_access = session.get(
                CustomerProjectAccess,
                access_id,
            )

            assert loaded_relationship is not None
            assert loaded_project is not None
            assert loaded_access is not None

            # The external user is assigned to the customer.
            assert loaded_relationship.user_id == external_user_id
            assert loaded_relationship.customer_id == customer_id

            # The project belongs to the same customer.
            assert loaded_project.customer_id == customer_id

            # The same external user has access to that project.
            assert loaded_access.user_id == external_user_id
            assert loaded_access.project_id == project_id

            # The access timestamps survive the PostgreSQL roundtrip.
            assert loaded_access.valid_from == valid_from
            assert loaded_access.valid_from.tzinfo is not None

            assert loaded_access.valid_until == valid_until
            assert loaded_access.valid_until.tzinfo is not None

            # The access is active and was created by the internal user.
            assert loaded_access.active is True
            assert loaded_access.created_from == internal_user_id

            # Audit timestamps are timezone-aware.
            assert loaded_access.created_at.tzinfo is not None
            assert loaded_access.updated_at.tzinfo is not None
    finally:
        engine.dispose()


def test_postgresql_workspace_utc_roundtrip() -> None:
    """Workspace audit timestamps must survive a PostgreSQL UTC roundtrip."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with Session(engine) as session:
            user = User(
                login_identifier="postgres-workspace-user",
                display_name="PostgreSQL Workspace User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            customer = Customer(
                name="PostgreSQL Workspace Customer",
                customer_type=CustomerType.COMPANY,
            )

            session.add_all([user, customer])
            session.flush()

            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Workspace Project",
                status="ACTIVE",
            )

            session.add(project)
            session.flush()

            workspace = Workspace(
                project_id=project.id,
                workspace_type=WorkspaceType.INTERNAL,
                created_from=user.id,
            )

            session.add(workspace)
            session.commit()

            workspace_id = workspace.id

        with Session(engine) as session:
            loaded = session.get(Workspace, workspace_id)

            assert loaded is not None
            assert loaded.workspace_type is WorkspaceType.INTERNAL

            assert loaded.created_at.tzinfo is not None
            assert loaded.updated_at.tzinfo is not None

            assert loaded.created_at <= loaded.updated_at
    finally:
        engine.dispose()


def test_postgresql_project_supports_both_workspace_types() -> None:
    """A PostgreSQL project must support one internal and one customer workspace."""
    database_url = _database_url()
    config = _alembic_config(database_url)
    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with Session(engine) as session:
            user = User(
                login_identifier="postgres-workspace-types-user",
                display_name="PostgreSQL Workspace Types User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )
            customer = Customer(
                name="PostgreSQL Workspace Types Customer",
                customer_type=CustomerType.COMPANY,
            )

            session.add_all([user, customer])
            session.flush()

            project = Project(
                customer_id=customer.id,
                name="PostgreSQL Workspace Types Project",
                status="ACTIVE",
            )

            session.add(project)
            session.flush()

            project_id = project.id
            user_id = user.id

            internal_workspace = Workspace(
                project_id=project_id,
                workspace_type=WorkspaceType.INTERNAL,
                created_from=user_id,
            )
            customer_workspace = Workspace(
                project_id=project_id,
                workspace_type=WorkspaceType.CUSTOMER,
                created_from=user_id,
            )

            session.add_all(
                [
                    internal_workspace,
                    customer_workspace,
                ]
            )
            session.commit()

            internal_workspace_id = internal_workspace.id
            customer_workspace_id = customer_workspace.id

        with Session(engine) as session:
            loaded_internal = session.get(
                Workspace,
                internal_workspace_id,
            )
            loaded_customer = session.get(
                Workspace,
                customer_workspace_id,
            )

            assert loaded_internal is not None
            assert loaded_customer is not None

            assert loaded_internal.project_id == project_id
            assert loaded_customer.project_id == project_id

            assert loaded_internal.created_from == user_id
            assert loaded_customer.created_from == user_id

            assert loaded_internal.workspace_type is WorkspaceType.INTERNAL
            assert loaded_customer.workspace_type is WorkspaceType.CUSTOMER
    finally:
        engine.dispose()


def test_postgresql_permission_schema() -> None:
    """PostgreSQL must create the Permission schema correctly."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

        columns = {
            column["name"]: column for column in inspector.get_columns("permissions")
        }

        assert set(columns) == {"id", "identifier"}
        assert columns["id"]["nullable"] is False
        assert columns["identifier"]["nullable"] is False

        primary_key = inspector.get_pk_constraint("permissions")
        assert primary_key["constrained_columns"] == ["id"]

        unique_constraints = inspector.get_unique_constraints(
            "permissions",
        )

        assert any(
            constraint["name"] == "uq_permissions_identifier"
            and constraint["column_names"] == ["identifier"]
            for constraint in unique_constraints
        )
    finally:
        engine.dispose()


def test_postgresql_permission_catalog_is_seeded() -> None:
    """PostgreSQL must contain the complete canonical MVP catalogue."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with Session(engine) as session:
            identifiers = set(
                session.scalars(
                    select(Permission.identifier),
                ).all(),
            )

        assert identifiers == {
            "customer.read",
            "customer.write",
            "project.read",
            "project.write",
            "project.coordinate",
            "purchase.create",
            "purchase.grant",
            "document.read",
            "document.write",
            "document.sign",
            "schedule.view_availability",
            "schedule.view_details",
            "schedule.assignment_write",
            "schedule.assignment_request",
            "schedule.assignment_grant",
            "user.manage",
            "permission.manage",
        }
    finally:
        engine.dispose()


def test_postgresql_permission_roundtrip() -> None:
    """A Permission must survive a PostgreSQL session roundtrip."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        with Session(engine) as session:
            permission = Permission(
                identifier="test.permission.roundtrip",
            )

            session.add(permission)
            session.commit()

            permission_id = permission.id

        with Session(engine) as session:
            loaded = session.get(Permission, permission_id)

            assert loaded is not None
            assert loaded.id == permission_id
            assert loaded.identifier == "test.permission.roundtrip"
    finally:
        engine.dispose()


def test_postgresql_permission_grant_schema() -> None:
    """PostgreSQL must create the PermissionGrant schema correctly."""
    database_url = _database_url()
    config = _alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)

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
        assert columns["created_at"]["nullable"] is False
        assert columns["updated_at"]["nullable"] is False

        foreign_keys = inspector.get_foreign_keys(
            "permission_grants",
        )

        foreign_key_map = {
            tuple(foreign_key["constrained_columns"]): foreign_key
            for foreign_key in foreign_keys
        }

        user_foreign_key = foreign_key_map[("user_id",)]
        assert user_foreign_key["referred_table"] == "users"
        assert user_foreign_key["referred_columns"] == ["id"]
        assert user_foreign_key["options"]["ondelete"] == "RESTRICT"

        permission_foreign_key = foreign_key_map[("permission_id",)]
        assert permission_foreign_key["referred_table"] == "permissions"
        assert permission_foreign_key["referred_columns"] == ["id"]
        assert permission_foreign_key["options"]["ondelete"] == "RESTRICT"

        granted_by_foreign_key = foreign_key_map[("granted_by_user_id",)]
        assert granted_by_foreign_key["referred_table"] == "users"
        assert granted_by_foreign_key["referred_columns"] == ["id"]
        assert granted_by_foreign_key["options"]["ondelete"] == "RESTRICT"

        indexes = inspector.get_indexes("permission_grants")
        index_names = {index["name"] for index in indexes}

        assert {
            "ix_permission_grants_user_id",
            "ix_permission_grants_permission_id",
            "ix_permission_grants_granted_by_user_id",
            "ix_permission_grants_user_permission_active",
            "ix_permission_grants_scope_active",
        }.issubset(index_names)

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


def test_postgresql_permission_grant_roundtrip() -> None:
    """A PermissionGrant must survive a PostgreSQL roundtrip."""
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
                login_identifier="postgres-permission-grant-user",
                display_name="PostgreSQL Permission Grant User",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )

            grantor = User(
                login_identifier="postgres-permission-grant-grantor",
                display_name="PostgreSQL Permission Grant Grantor",
                user_type=UserType.INTERNAL,
                role=UserRole.TECHNICIAN,
            )

            permission = Permission(
                identifier="purchase.create",
            )

            session.add_all(
                [
                    user,
                    grantor,
                    permission,
                ],
            )
            session.flush()

            grant = PermissionGrant(
                user_id=user.id,
                permission_id=permission.id,
                effect=PermissionGrantEffect.ALLOW,
                scope_type=PermissionGrantScopeType.PROJECT,
                scope_id=permission.id,
                constraint_type=PermissionGrantConstraintType.PURCHASE_LIMIT,
                constraint_value={
                    "amount": "2000.50",
                    "currency": "EUR",
                },
                valid_from=valid_from,
                valid_until=valid_until,
                active=True,
                granted_by_user_id=grantor.id,
            )

            session.add(grant)
            session.commit()

            grant_id = grant.id
            user_id = user.id
            grantor_id = grantor.id
            permission_id = permission.id

        with Session(engine) as session:
            loaded = session.get(
                PermissionGrant,
                grant_id,
            )

            assert loaded is not None
            assert loaded.user_id == user_id
            assert loaded.permission_id == permission_id
            assert loaded.granted_by_user_id == grantor_id

            assert loaded.effect is PermissionGrantEffect.ALLOW
            assert loaded.scope_type is PermissionGrantScopeType.PROJECT
            assert loaded.scope_id == permission_id

            assert (
                loaded.constraint_type is PermissionGrantConstraintType.PURCHASE_LIMIT
            )

            assert loaded.constraint_value == {
                "amount": "2000.50",
                "currency": "EUR",
            }

            assert loaded.valid_from == valid_from
            assert loaded.valid_from.tzinfo is not None

            assert loaded.valid_until == valid_until
            assert loaded.valid_until.tzinfo is not None

            assert loaded.active is True

            assert loaded.created_at.tzinfo is not None
            assert loaded.updated_at.tzinfo is not None
    finally:
        engine.dispose()
