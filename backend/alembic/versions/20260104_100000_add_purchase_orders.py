"""
Create purchase_orders and purchase_order_line_items tables.

Revision ID: 20260104_100000
Revises: 20260104_090000
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260104_100000"
down_revision: Union[str, None] = "20260104_090000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create purchase_orders and line_items tables with RLS."""
    
    # Create enum types
    op.execute("""
        CREATE TYPE purchase_order_status AS ENUM (
            'draft',
            'pending_approval',
            'approved',
            'ordered',
            'partially_received',
            'received',
            'cancelled'
        );
    """)
    
    op.execute("""
        CREATE TYPE purchase_order_priority AS ENUM (
            'low',
            'normal',
            'high',
            'urgent'
        );
    """)
    
    # Create purchase_orders table
    op.create_table(
        "purchase_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        # PO identification
        sa.Column("po_number", sa.String(50), nullable=False),
        # Supplier information
        sa.Column("supplier_name", sa.String(255), nullable=True),
        sa.Column("supplier_contact", sa.String(255), nullable=True),
        sa.Column("supplier_email", sa.String(255), nullable=True),
        sa.Column("supplier_phone", sa.String(50), nullable=True),
        # Status and priority
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "pending_approval",
                "approved",
                "ordered",
                "partially_received",
                "received",
                "cancelled",
                name="purchase_order_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low",
                "normal",
                "high",
                "urgent",
                name="purchase_order_priority",
                create_type=False,
            ),
            nullable=False,
            server_default="normal",
        ),
        # Dates
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_date", sa.DateTime(timezone=True), nullable=True),
        # Receiving location
        sa.Column("receiving_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Users
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Notes
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("external_reference", sa.String(100), nullable=True),
        # Totals
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("shipping_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        # Auto-generated flag
        sa.Column("auto_generated", sa.Boolean, nullable=False, server_default="false"),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["receiving_location_id"], ["locations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], ondelete="SET NULL"
        ),
    )
    
    # Create indexes for purchase_orders
    op.create_index("idx_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"])
    op.create_index("idx_purchase_orders_po_number", "purchase_orders", ["po_number"])
    op.create_index("idx_purchase_orders_status", "purchase_orders", ["status"])
    op.create_index("idx_purchase_orders_priority", "purchase_orders", ["priority"])
    op.create_index(
        "idx_purchase_orders_tenant_po_number",
        "purchase_orders",
        ["tenant_id", "po_number"],
        unique=True,
    )
    
    # Create purchase_order_line_items table
    op.create_table(
        "purchase_order_line_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Quantities
        sa.Column("quantity_ordered", sa.Integer, nullable=False, server_default="1"),
        sa.Column("quantity_received", sa.Integer, nullable=False, server_default="0"),
        # Pricing
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        # Notes
        sa.Column("notes", sa.Text, nullable=True),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["inventory_items.id"], ondelete="CASCADE"
        ),
    )
    
    # Create indexes for line items
    op.create_index("idx_po_line_items_tenant_id", "purchase_order_line_items", ["tenant_id"])
    op.create_index("idx_po_line_items_po_id", "purchase_order_line_items", ["purchase_order_id"])
    op.create_index("idx_po_line_items_item_id", "purchase_order_line_items", ["item_id"])
    
    # Enable RLS on purchase_orders
    op.execute("ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON purchase_orders
        FOR ALL TO synkventory_app
        USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
    """)
    
    # Admin bypass policy for purchase_orders
    op.execute("""
        CREATE POLICY admin_bypass_policy ON purchase_orders
        FOR ALL TO synkventory_admin
        USING (true)
        WITH CHECK (true);
    """)
    
    # Enable RLS on purchase_order_line_items
    op.execute("ALTER TABLE purchase_order_line_items ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON purchase_order_line_items
        FOR ALL TO synkventory_app
        USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
    """)
    
    # Admin bypass policy for line items
    op.execute("""
        CREATE POLICY admin_bypass_policy ON purchase_order_line_items
        FOR ALL TO synkventory_admin
        USING (true)
        WITH CHECK (true);
    """)
    
    # Grant permissions
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON purchase_orders TO synkventory_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON purchase_orders TO synkventory_admin;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON purchase_order_line_items TO synkventory_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON purchase_order_line_items TO synkventory_admin;")


def downgrade() -> None:
    """Drop purchase_orders and line_items tables."""
    # Drop policies
    op.execute("DROP POLICY IF EXISTS admin_bypass_policy ON purchase_order_line_items;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON purchase_order_line_items;")
    op.execute("DROP POLICY IF EXISTS admin_bypass_policy ON purchase_orders;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON purchase_orders;")
    
    # Drop tables
    op.drop_table("purchase_order_line_items")
    op.drop_table("purchase_orders")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS purchase_order_priority;")
    op.execute("DROP TYPE IF EXISTS purchase_order_status;")
