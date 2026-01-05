"""
Create bill_of_materials table for tracking item compositions.

Revision ID: 20260104_080000
Revises: 20260104_070000
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260104_080000"
down_revision: Union[str, None] = "20260104_070000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bill_of_materials table."""
    op.create_table(
        "bill_of_materials",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Parent/assembly item
        sa.Column("parent_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Component item
        sa.Column("component_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Quantity of component needed
        sa.Column("quantity_required", sa.Integer(), nullable=False, default=1),
        # Unit of measure
        sa.Column("unit_of_measure", sa.String(50), nullable=True, default="units"),
        # Notes
        sa.Column("notes", sa.Text(), nullable=True),
        # Display order
        sa.Column("display_order", sa.Integer(), nullable=True, default=0),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_item_id"], ["inventory_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["component_item_id"], ["inventory_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes for common queries
    op.create_index("ix_bom_tenant_id", "bill_of_materials", ["tenant_id"])
    op.create_index("ix_bom_parent_item", "bill_of_materials", ["parent_item_id"])
    op.create_index("ix_bom_component_item", "bill_of_materials", ["component_item_id"])
    op.create_index("ix_bom_created_by", "bill_of_materials", ["created_by"])
    op.create_index("ix_bom_created_at", "bill_of_materials", ["created_at"])
    
    # Unique constraint: one parent-component combination per tenant
    op.create_index(
        "ix_bom_tenant_parent_component",
        "bill_of_materials",
        ["tenant_id", "parent_item_id", "component_item_id"],
        unique=True,
    )

    # Enable RLS
    op.execute("ALTER TABLE bill_of_materials ENABLE ROW LEVEL SECURITY")

    # Tenant isolation policy (with NULLIF to handle empty strings)
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON bill_of_materials
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )

    # Admin bypass policy
    op.execute(
        """
        CREATE POLICY bill_of_materials_admin_bypass ON bill_of_materials
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )


def downgrade() -> None:
    """Drop bill_of_materials table."""
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON bill_of_materials")
    op.execute("DROP POLICY IF EXISTS bill_of_materials_admin_bypass ON bill_of_materials")
    
    # Drop indexes
    op.drop_index("ix_bom_tenant_parent_component", table_name="bill_of_materials")
    op.drop_index("ix_bom_created_at", table_name="bill_of_materials")
    op.drop_index("ix_bom_created_by", table_name="bill_of_materials")
    op.drop_index("ix_bom_component_item", table_name="bill_of_materials")
    op.drop_index("ix_bom_parent_item", table_name="bill_of_materials")
    op.drop_index("ix_bom_tenant_id", table_name="bill_of_materials")
    
    # Drop table
    op.drop_table("bill_of_materials")
