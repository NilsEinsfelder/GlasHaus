"""Tests for database constraints."""

from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.db.models import (
    Customer,
    ExternalRelationship,
    ExternalRelationshipType,
    User,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_external_relationship_valid_until_must_follow_valid_from(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """External relationship validity ranges must be logically ordered."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.OWNER,
        valid_from=datetime(2026, 2, 1, tzinfo=UTC),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "relationship_type",
    [
        ExternalRelationshipType.OWNER,
        ExternalRelationshipType.CONTACT,
    ],
)
def test_external_relationship_type_is_supported(
    db_session: Session,
    user: User,
    customer: Customer,
    relationship_type: ExternalRelationshipType,
) -> None:
    """Supported relationship types must persist successfully."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=relationship_type,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()

    assert relationship.relationship_type is relationship_type


def test_external_relationship_type_constraint_rejects_invalid_value(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """Unsupported relationship types must be rejected by the database."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type="INVALID",
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
