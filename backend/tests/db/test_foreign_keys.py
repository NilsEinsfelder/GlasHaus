"""Tests for external relationship foreign-key integrity."""

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


def test_external_relationship_requires_existing_user(
    db_session: Session,
    customer: Customer,
    user: User,
) -> None:
    """ExternalRelationship.user_id must reference an existing user."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=uuid7(),
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_external_relationship_requires_existing_customer(
    db_session: Session,
    user: User,
) -> None:
    """ExternalRelationship.customer_id must reference an existing customer."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=uuid7(),
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_external_relationship_requires_existing_creator(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """ExternalRelationship.created_from must reference an existing user."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.OWNER,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=uuid7(),
    )

    db_session.add(relationship)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
