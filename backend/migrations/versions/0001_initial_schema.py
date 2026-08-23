"""Create initial GlasHaus database schema."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial GlasHaus database schema."""
    op.create_table(
        "devices",
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("device_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("device_id"),
    )

    op.create_table(
        "sync_states",
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("next_local_sequence", sa.Integer(), nullable=False),
        sa.Column("sync_status", sa.String(length=32), nullable=False),
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_sync_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("last_sync_error", sa.String(length=2000), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )


def downgrade() -> None:
    """Drop the initial GlasHaus database schema."""
    op.drop_table("sync_states")
    op.drop_table("devices")