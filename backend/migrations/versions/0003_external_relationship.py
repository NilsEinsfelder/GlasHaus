"""Create external relationship persistence model."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_external_relationship"
down_revision: str | None = "0002_domain_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the external relationship persistence table."""
    op.create_table(
        "external_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column(
            "relationship_type",
            sa.String(length=32),
            nullable=False,
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
            "relationship_type IN ('OWNER', 'CONTACT')",
            name="ck_external_relationships_relationship_type",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_external_relationships_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
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
        "ix_external_relationships_user_id",
        "external_relationships",
        ["user_id"],
    )

    op.create_index(
        "ix_external_relationships_customer_id",
        "external_relationships",
        ["customer_id"],
    )

    op.create_index(
        "ix_external_relationships_created_from",
        "external_relationships",
        ["created_from"],
    )

    op.create_index(
        "ix_external_relationships_user_customer",
        "external_relationships",
        ["user_id", "customer_id"],
    )


def downgrade() -> None:
    """Drop the external relationship persistence table."""
    op.drop_index(
        "ix_external_relationships_user_customer",
        table_name="external_relationships",
    )
    op.drop_index(
        "ix_external_relationships_created_from",
        table_name="external_relationships",
    )
    op.drop_index(
        "ix_external_relationships_customer_id",
        table_name="external_relationships",
    )
    op.drop_index(
        "ix_external_relationships_user_id",
        table_name="external_relationships",
    )
    op.drop_table("external_relationships")