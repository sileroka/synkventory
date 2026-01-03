"""
Add admin bypass RLS policy

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-03
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add admin bypass policies to tenant-scoped tables.
    
    These policies allow operations when app.is_admin is set to 'true',
    enabling admin operations to bypass normal tenant isolation.
    """
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tenant_tables:
        # Add admin bypass policy
        op.execute(
            f"""
            CREATE POLICY {table}_admin_bypass ON {table}
                FOR ALL
                TO synkventory_app
                USING (current_setting('app.is_admin', true) = 'true')
                WITH CHECK (current_setting('app.is_admin', true) = 'true')
            """
        )

    # Also add for tenants table
    op.execute(
        """
        CREATE POLICY tenants_admin_bypass ON tenants
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )


def downgrade() -> None:
    """Remove admin bypass policies."""
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
        "tenants",
    ]

    for table in tenant_tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_admin_bypass ON {table}")
