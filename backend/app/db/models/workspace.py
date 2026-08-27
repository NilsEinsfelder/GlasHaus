"""Workspace persistence model."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User


class WorkspaceType(StrEnum):
    """Supported primary workspace types."""

    INTERNAL = "INTERNAL"
    CUSTOMER = "CUSTOMER"


class Workspace(Base, TimestampMixin):
    """Represent a primary security-boundary workspace of a project."""

    __tablename__ = "workspaces"
    __table_args__ = (
        CheckConstraint(
            "workspace_type IN ('INTERNAL', 'CUSTOMER')",
            name="ck_workspaces_workspace_type",
        ),
        UniqueConstraint(
            "project_id",
            "workspace_type",
            name="uq_workspaces_project_type",
        ),
        Index(
            "ix_workspaces_project_id",
            "project_id",
        ),
        Index(
            "ix_workspaces_created_from",
            "created_from",
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

    workspace_type: Mapped[WorkspaceType] = mapped_column(
        Enum(
            WorkspaceType,
            native_enum=False,
            length=32,
            name="workspacetype",
        ),
        nullable=False,
    )

    created_from: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        back_populates="workspaces",
    )

    created_from_user: Mapped[User] = relationship(
        foreign_keys=[created_from],
    )
