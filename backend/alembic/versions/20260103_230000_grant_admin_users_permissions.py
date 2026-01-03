"""Grant permissions on admin_users table to app user

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-03

"""

from alembic import op

# revision identifiers
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Grant permissions to app user for admin_users table
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON admin_users TO synkventory_app")


def downgrade() -> None:
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON admin_users FROM synkventory_app"
    )
