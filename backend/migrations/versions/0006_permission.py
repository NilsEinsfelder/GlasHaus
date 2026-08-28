"""Create permission persistence model."""

from collections.abc import Sequence
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision: str = "0006_permission"
down_revision: str | None = "0005_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PERMISSIONS = (
    (
        UUID("01a044e2-16fc-79ce-b798-ac69a576731f"),
        "customer.read",
    ),
    (
        UUID("01a044e2-16fc-7b44-ab5b-0e18a31a37d1"),
        "customer.write",
    ),
    (
        UUID("01a044e2-16fc-76bf-b2f6-600fad353a79"),
        "project.read",
    ),
    (
        UUID("01a044e2-16fc-7267-b61f-0be27e27e535"),
        "project.write",
    ),
    (
        UUID("01a044e2-16fc-732f-8257-2bf9a0355671"),
        "project.coordinate",
    ),
    (
        UUID("01a044e2-16fc-733a-9696-788da784887a"),
        "purchase.create",
    ),
    (
        UUID("01a044e2-16fc-7f75-afb9-a83cdae6ab3d"),
        "purchase.grant",
    ),
    (
        UUID("01a044e2-16fc-786f-8408-a6fbaa014ca6"),
        "document.read",
    ),
    (
        UUID("01a044e2-16fc-706c-8874-87b1338a7c44"),
        "document.write",
    ),
    (
        UUID("01a044e2-16fc-77be-994b-b9daa9c85bf6"),
        "document.sign",
    ),
    (
        UUID("01a044e2-16fc-7295-aa9b-ecbf58187d25"),
        "schedule.view_availability",
    ),
    (
        UUID("01a044e2-16fc-7d06-a67a-53c4c25c934d"),
        "schedule.view_details",
    ),
    (
        UUID("01a044e2-16fc-7856-b727-5c562a25221c"),
        "schedule.assignment_write",
    ),
    (
        UUID("01a044e2-16fc-74f8-a772-351e32a5a7d7"),
        "schedule.assignment_request",
    ),
    (
        UUID("01a044e2-16fc-790b-86a5-4a4aca34da73"),
        "schedule.assignment_grant",
    ),
    (
        UUID("01a044e2-16fc-7fa1-b6f5-2c4ffe397762"),
        "user.manage",
    ),
    (
        UUID("01a044e2-16fc-791a-9bed-888f32835b9e"),
        "permission.manage",
    ),
)


def upgrade() -> None:
    """Create the permission table and seed the canonical MVP catalogue."""
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "identifier",
            sa.String(length=255),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "identifier",
            name="uq_permissions_identifier",
        ),
    )

    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("identifier", sa.String(length=255)),
    )

    op.bulk_insert(
        permission_table,
        [
            {
                "id": permission_id,
                "identifier": identifier,
            }
            for permission_id, identifier in PERMISSIONS
        ],
    )


def downgrade() -> None:
    """Drop the permission table."""
    op.drop_table("permissions")
