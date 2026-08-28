"""Create permission grant persistence model."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_permission_grant"
down_revision: str | None = "0006_permission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the permission grant table."""
    op.create_table(
        "permission_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.Column(
            "effect",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column(
            "scope_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "scope_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "constraint_type",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "constraint_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "valid_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "granted_by_user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_permission_grants_effect",
        ),
        sa.CheckConstraint(
            (
                "scope_type IN "
                "('GLOBAL', 'PROJECT', 'WORKSPACE', 'DOCUMENT', 'USER')"
            ),
            name="ck_permission_grants_scope_type",
        ),
        sa.CheckConstraint(
            (
                "(scope_type = 'GLOBAL' AND scope_id IS NULL) "
                "OR "
                "(scope_type <> 'GLOBAL' AND scope_id IS NOT NULL)"
            ),
            name="ck_permission_grants_scope_consistency",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_permission_grants_valid_range",
        ),
        sa.CheckConstraint(
            (
                "constraint_type IS NOT NULL "
                "OR constraint_value IS NULL"
            ),
            name="ck_permission_grants_constraint_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_permission_grants_user_id",
        "permission_grants",
        ["user_id"],
    )

    op.create_index(
        "ix_permission_grants_permission_id",
        "permission_grants",
        ["permission_id"],
    )

    op.create_index(
        "ix_permission_grants_granted_by_user_id",
        "permission_grants",
        ["granted_by_user_id"],
    )

    op.create_index(
        "ix_permission_grants_user_permission_active",
        "permission_grants",
        ["user_id", "permission_id", "active"],
    )

    op.create_index(
        "ix_permission_grants_scope_active",
        "permission_grants",
        ["scope_type", "scope_id", "active"],
    )


def downgrade() -> None:
    """Drop the permission grant table."""
    op.drop_index(
        "ix_permission_grants_scope_active",
        table_name="permission_grants",
    )
    op.drop_index(
        "ix_permission_grants_user_permission_active",
        table_name="permission_grants",
    )
    op.drop_index(
        "ix_permission_grants_granted_by_user_id",
        table_name="permission_grants",
    )
    op.drop_index(
        "ix_permission_grants_permission_id",
        table_name="permission_grants",
    )
    op.drop_index(
        "ix_permission_grants_user_id",
        table_name="permission_grants",
    )
    op.drop_table("permission_grants")
