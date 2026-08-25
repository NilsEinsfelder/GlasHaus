"""Internal project assignment persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User


class ProjectAssignment(Base, TimestampMixin):
    """Represent an explicit internal user-to-project assignment."""

    __tablename__ = "project_assignments"

    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_project_assignments_valid_range",
        ),
        Index(
            "ix_project_assignments_user_id",
            "user_id",
        ),
        Index(
            "ix_project_assignments_project_id",
            "project_id",
        ),
        Index(
            "ix_project_assignments_project_user",
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

    assignment_context: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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

    project: Mapped[Project] = relationship(
        back_populates="assignments",
    )

    user: Mapped[User] = relationship(
        back_populates="project_assignments",
    )
