"""
Fix user email unique constraint to be per-tenant only

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop global email unique constraint, keep only tenant-scoped one.

    In a multi-tenant system, email uniqueness should be per-tenant.
    The same email can exist in different tenants.
    """
    # Drop global unique index on email if it exists
    op.execute("DROP INDEX IF EXISTS ix_users_email")

    # Ensure the composite unique index exists (tenant_id, email)
    # This was already created in initial migration but recreate if missing
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_tenant_email 
        ON users (tenant_id, email)
    """
    )


def downgrade() -> None:
    """Restore global email unique constraint (not recommended)."""
    # Note: This will fail if duplicate emails exist across tenants
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
