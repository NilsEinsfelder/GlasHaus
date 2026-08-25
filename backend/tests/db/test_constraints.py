"""Tests for database constraints."""

from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.db.models import (
    Customer,
    Employment,
    User,
    UserRole,
    UserType,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_login_identifier_is_unique(
    db_session: Session,
    user: User,
) -> None:
    """Duplicate login identifiers must be rejected."""
    duplicate = User(
        id=uuid7(),
        login_identifier=user.login_identifier,
        display_name="Another User",
        user_type=UserType.INTERNAL,
        role=UserRole.TECHNICIAN,
    )

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_employment_valid_until_must_follow_valid_from(
    db_session: Session,
    user: User,
) -> None:
    """Employment validity ranges must be logically ordered."""
    employment = Employment(
        id=uuid7(),
        user_id=user.id,
        hierarchy_level="LEVEL_1",
        employment_status="ACTIVE",
        valid_from=datetime(2026, 2, 1, tzinfo=UTC),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(employment)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_customer_type_constraint(
    db_session: Session,
) -> None:
    """Customer type must be one of the supported values."""
    customer = Customer(
        id=uuid7(),
        customer_type="INVALID",
        name="Invalid Customer",
    )

    db_session.add(customer)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
