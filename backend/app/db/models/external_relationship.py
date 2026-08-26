"""External relationship persistence model."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.customer import Customer
    from app.db.models.user import User


class ExternalRelationshipType(StrEnum):
    """Supported User-to-Customer relationship types."""

    OWNER = "OWNER"
    CONTACT = "CONTACT"


class ExternalRelationship(Base, TimestampMixin):
    """Represent an explicit business relationship between a User and Customer."""

    __tablename__ = "external_relationships"

    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('OWNER', 'CONTACT')",
            name="ck_external_relationships_relationship_type",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_external_relationships_valid_range",
        ),
        Index(
            "ix_external_relationships_user_id",
            "user_id",
        ),
        Index(
            "ix_external_relationships_customer_id",
            "customer_id",
        ),
        Index(
            "ix_external_relationships_created_from",
            "created_from",
        ),
        Index(
            "ix_external_relationships_user_customer",
            "user_id",
            "customer_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    relationship_type: Mapped[ExternalRelationshipType] = mapped_column(
        Enum(
            ExternalRelationshipType,
            native_enum=False,
            length=32,
            name="externalrelationshiptype",
        ),
        nullable=False,
    )

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    created_from: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
        back_populates="external_relationships",
    )

    customer: Mapped[Customer] = relationship(
        back_populates="external_relationships",
    )

    created_from_user: Mapped[User] = relationship(
        foreign_keys=[created_from],
    )
