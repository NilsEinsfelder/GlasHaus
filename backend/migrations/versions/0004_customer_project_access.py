"""Create customer project access persistence model."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_customer_project_access"
down_revision: str | None = "0003_external_relationship"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the customer project access table."""
    op.create_table(
        "customer_project_accesses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
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
            "created_from",
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
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_customer_project_accesses_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_from"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_customer_project_accesses_user_id",
        "customer_project_accesses",
        ["user_id"],
    )

    op.create_index(
        "ix_customer_project_accesses_project_id",
        "customer_project_accesses",
        ["project_id"],
    )

    op.create_index(
        "ix_customer_project_accesses_project_user",
        "customer_project_accesses",
        ["project_id", "user_id"],
    )


def downgrade() -> None:
    """Drop the customer project access table."""
    op.drop_index(
        "ix_customer_project_accesses_project_user",
        table_name="customer_project_accesses",
    )
    op.drop_index(
        "ix_customer_project_accesses_project_id",
        table_name="customer_project_accesses",
    )
    op.drop_index(
        "ix_customer_project_accesses_user_id",
        table_name="customer_project_accesses",
    )
    op.drop_table("customer_project_accesses")
