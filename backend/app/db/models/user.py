"""User persistence model."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Enum, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.employment import Employment
    from app.db.models.project_assignment import ProjectAssignment


class UserType(StrEnum):
    """Supported GlasHaus user types."""

    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class UserRole(StrEnum):
    """Known GlasHaus roles."""

    TECHNICIAN = "TECHNICIAN"
    OFFICE = "OFFICE"
    CUSTOMER = "CUSTOMER"
    TAX_ADVISOR = "TAX_ADVISOR"


class User(Base, TimestampMixin):
    """Represent a human GlasHaus identity."""

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "login_identifier",
            name="uq_users_login_identifier",
        ),
        CheckConstraint(
            "user_type IN ('INTERNAL', 'EXTERNAL')",
            name="ck_users_user_type",
        ),
        Index(
            "ix_users_email",
            "email",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )

    login_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        nullable=True,
    )

    user_type: Mapped[UserType] = mapped_column(
        Enum(
            UserType,
            native_enum=False,
            length=32,
            name="usertype",
        ),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            length=64,
            name="userrole",
        ),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    employments: Mapped[list[Employment]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )

    project_assignments: Mapped[list[ProjectAssignment]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )
