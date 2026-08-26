"""Customer project access persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User


class CustomerProjectAccess(Base, TimestampMixin):
    """Represent explicit external user access to a customer project."""

    __tablename__ = "customer_project_accesses"

    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_customer_project_accesses_valid_range",
        ),
        Index(
            "ix_customer_project_accesses_user_id",
            "user_id",
        ),
        Index(
            "ix_customer_project_accesses_project_id",
            "project_id",
        ),
        Index(
            "ix_customer_project_accesses_project_user",
            "project_id",
            "user_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
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

    project: Mapped[Project] = relationship(
        back_populates="customer_project_accesses",
    )

    user: Mapped[User] = relationship(
        back_populates="customer_project_accesses",
        foreign_keys=[user_id],
    )
