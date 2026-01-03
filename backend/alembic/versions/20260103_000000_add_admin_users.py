"""Add admin_users table for admin portal

Revision ID: 0003
Revises: 20260103_103839
Create Date: 2026-01-03

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0003"
down_revision = "20260103_103839"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admin_users table (not tenant-scoped)
    op.create_table(
        "admin_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create unique index on email
    op.create_index("idx_admin_users_email", "admin_users", ["email"], unique=True)

    # NOTE: No RLS on admin_users - they are not tenant-scoped


def downgrade() -> None:
    op.drop_index("idx_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
