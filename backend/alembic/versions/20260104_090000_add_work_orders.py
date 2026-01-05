"""
Create work_orders table for tracking production builds.

Revision ID: 20260104_090000
Revises: 20260104_080000
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260104_090000"
down_revision: Union[str, None] = "20260104_080000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create work_orders table with RLS."""
    
    # Create enum types
    op.execute("""
        CREATE TYPE work_order_status AS ENUM (
            'draft',
            'pending',
            'in_progress',
            'on_hold',
            'completed',
            'cancelled'
        );
    """)
    
    op.execute("""
        CREATE TYPE work_order_priority AS ENUM (
            'low',
            'normal',
            'high',
            'urgent'
        );
    """)
    
    # Create work_orders table
    op.create_table(
        "work_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Work order identification
        sa.Column("work_order_number", sa.String(50), nullable=False),
        # Assembly item to build
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Quantities
        sa.Column("quantity_ordered", sa.Integer(), nullable=False, default=1),
        sa.Column("quantity_completed", sa.Integer(), nullable=False, default=0),
        sa.Column("quantity_scrapped", sa.Integer(), nullable=False, default=0),
        # Status and priority
        sa.Column(
            "status",
            postgresql.ENUM("draft", "pending", "in_progress", "on_hold", "completed", "cancelled", name="work_order_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM("low", "normal", "high", "urgent", name="work_order_priority", create_type=False),
            nullable=False,
            server_default="normal",
        ),
        # Dates
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_date", sa.DateTime(timezone=True), nullable=True),
        # Output location
        sa.Column("output_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Assigned user
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Notes
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Cost tracking
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(12, 2), nullable=True),
        # Audit fields
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
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["output_location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes for common queries
    op.create_index("ix_work_orders_tenant_id", "work_orders", ["tenant_id"])
    op.create_index("ix_work_orders_item_id", "work_orders", ["item_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_priority", "work_orders", ["priority"])
    op.create_index("ix_work_orders_due_date", "work_orders", ["due_date"])
    op.create_index("ix_work_orders_assigned_to", "work_orders", ["assigned_to_id"])
    op.create_index("ix_work_orders_created_at", "work_orders", ["created_at"])
    
    # Unique constraint: work order number per tenant
    op.create_index(
        "ix_work_orders_tenant_number",
        "work_orders",
        ["tenant_id", "work_order_number"],
        unique=True,
    )

    # Enable Row Level Security
    op.execute("ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;")

    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON work_orders
        FOR ALL TO synkventory_app
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
    """)

    # Grant permissions to the application role
    op.execute("GRANT ALL ON work_orders TO synkventory_app;")


def downgrade() -> None:
    """Drop work_orders table and enums."""
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON work_orders;")
    op.drop_table("work_orders")
    op.execute("DROP TYPE IF EXISTS work_order_status;")
    op.execute("DROP TYPE IF EXISTS work_order_priority;")
