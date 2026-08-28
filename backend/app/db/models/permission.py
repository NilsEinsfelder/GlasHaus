"""Permission persistence model."""

from __future__ import annotations

from uuid import UUID, uuid7

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Permission(Base):
    """Represent a canonical application-defined permission."""

    __tablename__ = "permissions"

    __table_args__ = (
        UniqueConstraint(
            "identifier",
            name="uq_permissions_identifier",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
