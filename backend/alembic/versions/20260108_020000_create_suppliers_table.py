"""
Create suppliers table for centralized vendor/supplier management.

Revision ID: 20260108_020000
Revises: 20260108_010000
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260108_020000"
down_revision: Union[str, None] = "20260108_010000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create suppliers table with RLS policies."""
    
    # Create suppliers table
    op.create_table(
        "suppliers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        
        # Supplier identification
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=True),
        
        # Contact information
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        
        # Address fields
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        
        # Additional information
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        
        # Audit timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        
        # Foreign keys
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Create indices for fast lookups
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"])
    op.create_index("ix_suppliers_tenant_name", "suppliers", ["tenant_id", "name"])
    op.create_index("ix_suppliers_is_active", "suppliers", ["is_active"])
    op.create_index("ix_suppliers_email", "suppliers", ["email"])

    # Create unique constraint on (tenant_id, name) to prevent duplicate suppliers
    op.create_unique_constraint(
        "uq_suppliers_tenant_name",
        "suppliers",
        ["tenant_id", "name"]
    )

    # Enable Row Level Security
    op.execute("ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY")

    # Create tenant isolation policy (matches pattern from other tables)
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON suppliers
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )

    # Create admin bypass policy
    op.execute(
        """
        CREATE POLICY suppliers_admin_bypass ON suppliers
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )

    # Grant permissions to app user
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON suppliers TO synkventory_app")


def downgrade() -> None:
    """Drop suppliers table and related policies."""
    
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS suppliers_admin_bypass ON suppliers")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON suppliers")
    
    # Drop the table (cascades to indices and constraints)
    op.drop_table("suppliers")
