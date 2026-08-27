"""Create workspace persistence model."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_workspace"
down_revision: str | None = "0004_customer_project_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the workspace table."""
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column(
            "workspace_type",
            sa.String(length=32),
            nullable=False,
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
            "workspace_type IN ('INTERNAL', 'CUSTOMER')",
            name="ck_workspaces_workspace_type",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_from"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "workspace_type",
            name="uq_workspaces_project_type",
        ),
    )

    op.create_index(
        "ix_workspaces_project_id",
        "workspaces",
        ["project_id"],
    )

    op.create_index(
        "ix_workspaces_created_from",
        "workspaces",
        ["created_from"],
    )


def downgrade() -> None:
    """Drop the workspace table."""
    op.drop_index(
        "ix_workspaces_created_from",
        table_name="workspaces",
    )
    op.drop_index(
        "ix_workspaces_project_id",
        table_name="workspaces",
    )
    op.drop_table("workspaces")
