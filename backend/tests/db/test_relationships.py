"""Tests for SQLAlchemy external relationship mappings."""

from datetime import UTC, datetime
from uuid import uuid7

from app.db.models import (
    Customer,
    ExternalRelationship,
    ExternalRelationshipType,
    User,
)
from sqlalchemy.orm import Session


def test_user_has_external_relationship(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """User.external_relationships must expose related records."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(user)

    assert relationship in user.external_relationships
    assert relationship.user is user


def test_customer_has_external_relationship(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """Customer.external_relationships must expose related records."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.OWNER,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(customer)

    assert relationship in customer.external_relationships
    assert relationship.customer is customer


def test_external_relationship_exposes_creator_user(
    db_session: Session,
    user: User,
    customer: Customer,
) -> None:
    """created_from must resolve to the creating User."""
    relationship = ExternalRelationship(
        id=uuid7(),
        user_id=user.id,
        customer_id=customer.id,
        relationship_type=ExternalRelationshipType.CONTACT,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        created_from=user.id,
    )

    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(relationship)

    assert relationship.created_from_user is user
