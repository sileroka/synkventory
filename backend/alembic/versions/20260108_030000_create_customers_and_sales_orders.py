"""
Create customers, sales_orders, and sales_order_line_items tables.

Revision ID: 20260108_030000
Revises: 20260108_020000
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260108_030000"
down_revision: Union[str, None] = "20260108_020000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create customers and sales order tables with RLS policies."""

    # Create enum types for sales orders
    op.execute(
        """
        CREATE TYPE sales_order_status AS ENUM (
            'draft',
            'confirmed',
            'picked',
            'shipped',
            'cancelled'
        );
        """
    )

    op.execute(
        """
        CREATE TYPE sales_order_priority AS ENUM (
            'low',
            'normal',
            'high'
        );
        """
    )

    # customers table
    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("shipping_address", postgresql.JSONB, nullable=True),
        sa.Column("billing_address", postgresql.JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_index("ix_customers_is_active", "customers", ["is_active"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_unique_constraint(
        "uq_customers_tenant_name", "customers", ["tenant_id", "name"]
    )

    # sales_orders table
    op.create_table(
        "sales_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "confirmed",
                "picked",
                "shipped",
                "cancelled",
                name="sales_order_status",
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
                name="sales_order_priority",
                create_type=False,
            ),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_ship_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "shipping_cost", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_sales_orders_tenant_id", "sales_orders", ["tenant_id"])
    op.create_index("ix_sales_orders_status", "sales_orders", ["status"])
    op.create_index("ix_sales_orders_priority", "sales_orders", ["priority"])
    op.create_index("ix_sales_orders_customer_id", "sales_orders", ["customer_id"])
    op.create_index(
        "ix_sales_orders_tenant_order_number",
        "sales_orders",
        ["tenant_id", "order_number"],
        unique=True,
    )

    # sales_order_line_items table
    op.create_table(
        "sales_order_line_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sales_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quantity_ordered", sa.Integer, nullable=False, server_default="1"),
        sa.Column("quantity_shipped", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["sales_order_id"], ["sales_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["inventory_items.id"], ondelete="SET NULL"
        ),
    )

    op.create_index(
        "ix_sales_order_line_items_tenant_id",
        "sales_order_line_items",
        ["tenant_id"],
    )
    op.create_index(
        "ix_sales_order_line_items_order_id",
        "sales_order_line_items",
        ["sales_order_id"],
    )
    op.create_index(
        "ix_sales_order_line_items_item_id",
        "sales_order_line_items",
        ["item_id"],
    )

    # Enable Row Level Security and policies
    op.execute("ALTER TABLE customers ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON customers
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )
    op.execute(
        """
        CREATE POLICY customers_admin_bypass ON customers
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )
    op.execute("GRANT ALL ON customers TO synkventory_app;")

    op.execute("ALTER TABLE sales_orders ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON sales_orders
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )
    op.execute(
        """
        CREATE POLICY sales_orders_admin_bypass ON sales_orders
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )
    op.execute("GRANT ALL ON sales_orders TO synkventory_app;")

    op.execute("ALTER TABLE sales_order_line_items ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON sales_order_line_items
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )
    op.execute(
        """
        CREATE POLICY sales_order_line_items_admin_bypass ON sales_order_line_items
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )
    op.execute("GRANT ALL ON sales_order_line_items TO synkventory_app;")


def downgrade() -> None:
    """Drop sales order and customer tables and types."""

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS sales_order_line_items_admin_bypass ON sales_order_line_items;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON sales_order_line_items;")
    op.execute("DROP POLICY IF EXISTS sales_orders_admin_bypass ON sales_orders;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON sales_orders;")
    op.execute("DROP POLICY IF EXISTS customers_admin_bypass ON customers;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON customers;")

    # Drop tables
    op.drop_table("sales_order_line_items")
    op.drop_table("sales_orders")
    op.drop_table("customers")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sales_order_priority;")
    op.execute("DROP TYPE IF EXISTS sales_order_status;")
