"""Project persistence model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid7

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.customer import Customer
    from app.db.models.customer_project_access import CustomerProjectAccess
    from app.db.models.project_assignment import ProjectAssignment
    from app.db.models.workspace import Workspace


class Project(Base, TimestampMixin):
    """Represent a customer project."""

    __tablename__ = "projects"

    __table_args__ = (
        Index(
            "ix_projects_customer_id",
            "customer_id",
        ),
        Index(
            "ix_projects_name",
            "name",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    address_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="projects",
    )

    assignments: Mapped[list[ProjectAssignment]] = relationship(
        back_populates="project",
        passive_deletes=True,
    )

    customer_project_accesses: Mapped[list[CustomerProjectAccess]] = relationship(
        back_populates="project",
        passive_deletes=True,
    )

    workspaces: Mapped[list[Workspace]] = relationship(
        back_populates="project",
        passive_deletes=True,
    )
