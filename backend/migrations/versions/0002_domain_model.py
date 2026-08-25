"""Create the core GlasHaus domain persistence model."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_domain_model"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the core domain persistence tables."""

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "login_identifier",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "user_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
            "user_type IN ('INTERNAL', 'EXTERNAL')",
            name="ck_users_user_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "login_identifier",
            name="uq_users_login_identifier",
        ),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
    )

    op.create_table(
        "employments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "hierarchy_level",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "employment_status",
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
            name="ck_employments_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_employments_user_valid_from",
        "employments",
        ["user_id", "valid_from"],
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "customer_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "contact_metadata",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
            "customer_type IN ('COMPANY', 'PRIVATE')",
            name="ck_customers_customer_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_customers_name",
        "customers",
        ["name"],
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "address_metadata",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_projects_customer_id",
        "projects",
        ["customer_id"],
    )

    op.create_index(
        "ix_projects_name",
        "projects",
        ["name"],
    )

    op.create_table(
        "project_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "assignment_context",
            sa.String(length=255),
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
            name="ck_project_assignments_valid_range",
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_project_assignments_user_id",
        "project_assignments",
        ["user_id"],
    )

    op.create_index(
        "ix_project_assignments_project_id",
        "project_assignments",
        ["project_id"],
    )

    op.create_index(
        "ix_project_assignments_project_user",
        "project_assignments",
        ["project_id", "user_id"],
    )


def downgrade() -> None:
    """Drop the core domain persistence tables."""

    op.drop_index(
        "ix_project_assignments_project_user",
        table_name="project_assignments",
    )
    op.drop_index(
        "ix_project_assignments_project_id",
        table_name="project_assignments",
    )
    op.drop_index(
        "ix_project_assignments_user_id",
        table_name="project_assignments",
    )
    op.drop_table("project_assignments")

    op.drop_index(
        "ix_projects_name",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_customer_id",
        table_name="projects",
    )
    op.drop_table("projects")

    op.drop_index(
        "ix_customers_name",
        table_name="customers",
    )
    op.drop_table("customers")

    op.drop_index(
        "ix_employments_user_valid_from",
        table_name="employments",
    )
    op.drop_table("employments")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")