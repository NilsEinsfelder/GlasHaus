"""Permission grant persistence model."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import JSON, CheckConstraint, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.permission import Permission
    from app.db.models.user import User


type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)


class PermissionGrantEffect(StrEnum):
    """Supported permission grant effects."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class PermissionGrantScopeType(StrEnum):
    """Supported permission grant scope types."""

    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    WORKSPACE = "WORKSPACE"
    CUSTOMER = "CUSTOMER"
    USER = "USER"


class PermissionGrantConstraintType(StrEnum):
    """Supported permission grant constraint types."""

    PURCHASE_LIMIT = "purchase_limit"


class PermissionGrant(Base, TimestampMixin):
    """Represent an explicit, scoped permission grant or restriction."""

    __tablename__ = "permission_grants"

    __table_args__ = (
        CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_permission_grants_effect",
        ),
        CheckConstraint(
            ("scope_type IN ('GLOBAL', 'PROJECT', 'WORKSPACE', 'CUSTOMER', 'USER')"),
            name="ck_permission_grants_scope_type",
        ),
        CheckConstraint(
            (
                "(scope_type = 'GLOBAL' AND scope_id IS NULL) "
                "OR "
                "(scope_type <> 'GLOBAL' AND scope_id IS NOT NULL)"
            ),
            name="ck_permission_grants_scope_consistency",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_permission_grants_valid_range",
        ),
        CheckConstraint(
            """
            (
                constraint_type IS NULL
                AND constraint_value IS NULL
            )
            OR (
                constraint_type IS NOT NULL
                AND constraint_type = 'purchase_limit'
            )
            """,
            name="ck_permission_grants_constraint_consistency",
        ),
        Index(
            "ix_permission_grants_user_id",
            "user_id",
        ),
        Index(
            "ix_permission_grants_permission_id",
            "permission_id",
        ),
        Index(
            "ix_permission_grants_granted_by_user_id",
            "granted_by_user_id",
        ),
        Index(
            "ix_permission_grants_user_permission_active",
            "user_id",
            "permission_id",
            "active",
        ),
        Index(
            "ix_permission_grants_scope_active",
            "scope_type",
            "scope_id",
            "active",
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

    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "permissions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    effect: Mapped[PermissionGrantEffect] = mapped_column(
        Enum(
            PermissionGrantEffect,
            native_enum=False,
            length=16,
            name="permissiongranteffect",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    scope_type: Mapped[PermissionGrantScopeType] = mapped_column(
        Enum(
            PermissionGrantScopeType,
            native_enum=False,
            length=32,
            name="permissiongrantscopetype",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    scope_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    constraint_type: Mapped[PermissionGrantConstraintType | None] = mapped_column(
        Enum(
            PermissionGrantConstraintType,
            native_enum=False,
            length=32,
            name="permissiongrantconstrainttype",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
    )

    constraint_value: Mapped[JSONValue] = mapped_column(
        JSON(none_as_null=True),
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

    granted_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
    )

    permission: Mapped[Permission] = relationship()

    granted_by_user: Mapped[User] = relationship(
        foreign_keys=[granted_by_user_id],
    )
