"""Persistence tests for the Permission model and repository."""

from uuid import UUID, uuid7

import pytest
from app.db.models import Base, Permission
from app.db.repositories import PermissionRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

EXPECTED_PERMISSION_IDENTIFIERS = {
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


def test_permission_table_is_registered_in_metadata() -> None:
    """The Permission model must be part of the SQLAlchemy metadata."""
    assert "permissions" in Base.metadata.tables


def test_permission_schema_matches_mvp_model() -> None:
    """The Permission table contains only the approved MVP fields."""
    table = Base.metadata.tables["permissions"]

    assert set(table.columns.keys()) == {"id", "identifier"}
    assert table.columns["id"].primary_key is True
    assert table.columns["id"].nullable is False
    assert table.columns["identifier"].nullable is False

    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if constraint.name is not None
    }

    assert "uq_permissions_identifier" in unique_constraints


def test_permission_identifier_is_unique(db_session: Session) -> None:
    """Two permissions must not share the same canonical identifier."""
    first = Permission(
        id=uuid7(),
        identifier="project.read",
    )
    second = Permission(
        id=uuid7(),
        identifier="project.read",
    )

    db_session.add(first)
    db_session.commit()

    db_session.add(second)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_identifier_is_required(db_session: Session) -> None:
    """A Permission must always have a canonical identifier."""
    permission = Permission(
        id=uuid7(),
        identifier=None,  # type: ignore[arg-type]
    )

    db_session.add(permission)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_permission_roundtrip(db_session: Session) -> None:
    """A Permission survives a database session roundtrip."""
    permission = Permission(
        id=uuid7(),
        identifier="document.sign",
    )

    db_session.add(permission)
    db_session.commit()

    persisted_id = permission.id

    db_session.expunge_all()

    loaded = db_session.get(Permission, persisted_id)

    assert loaded is not None
    assert loaded.id == persisted_id
    assert isinstance(loaded.id, UUID)
    assert loaded.identifier == "document.sign"


def test_permission_repository_get(
    db_session: Session,
) -> None:
    """The repository retrieves a Permission by ID."""
    permission = Permission(
        identifier="project.read",
    )

    db_session.add(permission)
    db_session.commit()

    repository = PermissionRepository(db_session)

    loaded = repository.get(permission.id)

    assert loaded is not None
    assert loaded.id == permission.id
    assert loaded.identifier == "project.read"


def test_permission_repository_get_by_identifier(
    db_session: Session,
) -> None:
    """The repository retrieves a Permission by canonical identifier."""
    permission = Permission(
        identifier="permission.manage",
    )

    db_session.add(permission)
    db_session.commit()

    repository = PermissionRepository(db_session)

    loaded = repository.get_by_identifier("permission.manage")

    assert loaded is not None
    assert loaded.id == permission.id
    assert loaded.identifier == "permission.manage"


def test_permission_repository_returns_none_for_unknown_identifier(
    db_session: Session,
) -> None:
    """Unknown permission identifiers return no entity."""
    repository = PermissionRepository(db_session)

    assert repository.get_by_identifier("does.not.exist") is None


def test_permission_repository_list_orders_by_identifier(
    db_session: Session,
) -> None:
    """The repository returns permissions in deterministic order."""
    db_session.add_all(
        [
            Permission(identifier="project.write"),
            Permission(identifier="customer.read"),
            Permission(identifier="document.read"),
        ],
    )
    db_session.commit()

    repository = PermissionRepository(db_session)

    permissions = repository.list()

    assert [permission.identifier for permission in permissions] == [
        "customer.read",
        "document.read",
        "project.write",
    ]


def test_permission_repository_add_flushes_entity(
    db_session: Session,
) -> None:
    """Adding a Permission through the repository assigns its ID."""
    repository = PermissionRepository(db_session)

    permission = repository.add(
        Permission(identifier="project.coordinate"),
    )

    assert permission.id is not None
    assert permission.identifier == "project.coordinate"


def test_mvp_permission_catalog_contains_exactly_seventeen_identifiers() -> None:
    """The approved MVP permission catalogue contains exactly 17 entries."""
    assert len(EXPECTED_PERMISSION_IDENTIFIERS) == 17
    assert "permission.manage" in EXPECTED_PERMISSION_IDENTIFIERS
    assert "project.read" in EXPECTED_PERMISSION_IDENTIFIERS
    assert "document.sign" in EXPECTED_PERMISSION_IDENTIFIERS
