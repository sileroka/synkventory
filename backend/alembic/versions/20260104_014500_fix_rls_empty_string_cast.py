"""
Fix RLS policies to handle empty tenant_id strings

The original tenant isolation policies try to cast current_setting('app.current_tenant_id', true)
directly to UUID. When this setting is empty (admin requests), the cast fails.

This migration updates the policies to use NULLIF to handle empty strings gracefully.

Revision ID: 0007
Revises: 0006
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update tenant isolation policies to handle empty string tenant_id.

    Using NULLIF converts empty string to NULL, and tenant_id = NULL is always false,
    which correctly denies access when no tenant context is set (unless admin bypass applies).
    """
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tenant_tables:
        # Drop the old policy
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")

        # Create new policy with NULLIF to handle empty strings
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_policy ON {table}
                FOR ALL
                TO synkventory_app
                USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            """
        )


def downgrade() -> None:
    """Revert to original tenant isolation policies (without NULLIF)."""
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tenant_tables:
        # Drop the new policy
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")

        # Recreate original policy
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_policy ON {table}
                FOR ALL
                TO synkventory_app
                USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
                WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
            """
        )
