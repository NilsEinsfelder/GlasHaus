"""Customer persistence model."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid7

from sqlalchemy import JSON, CheckConstraint, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.external_relationship import ExternalRelationship
    from app.db.models.project import Project


class CustomerType(StrEnum):
    """Supported customer types."""

    COMPANY = "COMPANY"
    PRIVATE = "PRIVATE"


class Customer(Base, TimestampMixin):
    """Represent a GlasHaus customer business entity."""

    __tablename__ = "customers"

    __table_args__ = (
        CheckConstraint(
            "customer_type IN ('COMPANY', 'PRIVATE')",
            name="ck_customers_customer_type",
        ),
        Index(
            "ix_customers_name",
            "name",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    customer_type: Mapped[CustomerType] = mapped_column(
        Enum(
            CustomerType,
            native_enum=False,
            length=32,
            name="customertype",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    contact_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    projects: Mapped[list[Project]] = relationship(
        back_populates="customer",
        passive_deletes=True,
    )

    external_relationships: Mapped[list[ExternalRelationship]] = relationship(
        back_populates="customer",
        passive_deletes=True,
    )
