"""Tests for customer project access persistence."""

from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.db.models import (
    CustomerProjectAccess,
    User,
    UserRole,
    UserType,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _external_user(db_session: Session) -> User:
    """Create an external customer user for persistence tests."""
    entity = User(
        id=uuid7(),
        login_identifier=f"external-{uuid7()}",
        display_name="External Customer User",
        email=f"{uuid7()}@example.com",
        user_type=UserType.EXTERNAL,
        role=UserRole.CUSTOMER,
        active=True,
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


def test_customer_project_access_roundtrip(
    db_session: Session,
    user: User,
    project,
) -> None:
    """CustomerProjectAccess must persist all model fields."""
    external_user = _external_user(db_session)

    valid_from = datetime(2026, 1, 1, tzinfo=UTC)
    valid_until = datetime(2026, 12, 31, tzinfo=UTC)

    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=project.id,
        user_id=external_user.id,
        valid_from=valid_from,
        valid_until=valid_until,
        active=True,
        created_from=user.id,
    )

    db_session.add(access)
    db_session.commit()
    db_session.refresh(access)

    assert access.project_id == project.id
    assert access.user_id == external_user.id
    assert access.valid_from.replace(tzinfo=UTC) == valid_from
    assert access.valid_until.replace(tzinfo=UTC) == valid_until
    assert access.active is True
    assert access.created_from == user.id
    assert access.created_at is not None
    assert access.updated_at is not None


def test_customer_project_access_valid_until_must_follow_valid_from(
    db_session: Session,
    user: User,
    project,
) -> None:
    """CustomerProjectAccess validity ranges must be logically ordered."""
    external_user = _external_user(db_session)

    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=project.id,
        user_id=external_user.id,
        valid_from=datetime(2026, 2, 1, tzinfo=UTC),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=user.id,
    )

    db_session.add(access)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_customer_project_access_allows_open_ended_validity(
    db_session: Session,
    user: User,
    project,
) -> None:
    """CustomerProjectAccess may remain valid without an end date."""
    external_user = _external_user(db_session)

    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=project.id,
        user_id=external_user.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
        active=True,
        created_from=user.id,
    )

    db_session.add(access)
    db_session.commit()

    assert access.valid_until is None


def test_customer_project_access_requires_existing_project(
    db_session: Session,
    user: User,
) -> None:
    """project_id must reference an existing project."""
    external_user = _external_user(db_session)

    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=uuid7(),
        user_id=external_user.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=user.id,
    )

    db_session.add(access)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_customer_project_access_requires_existing_user(
    db_session: Session,
    user: User,
    project,
) -> None:
    """user_id must reference an existing user."""
    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=project.id,
        user_id=uuid7(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=user.id,
    )

    db_session.add(access)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_customer_project_access_requires_existing_creator(
    db_session: Session,
    project,
) -> None:
    """created_from must reference an existing user."""
    external_user = _external_user(db_session)

    access = CustomerProjectAccess(
        id=uuid7(),
        project_id=project.id,
        user_id=external_user.id,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        active=True,
        created_from=uuid7(),
    )

    db_session.add(access)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
