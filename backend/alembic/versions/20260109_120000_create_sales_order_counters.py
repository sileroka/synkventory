"""
Create sales_order_counters table for tenant-scoped sales order numbering.

Revision ID: 20260109_120000_create_sales_order_counters
Revises: 20260106_010000_fix_bom_permissions
Create Date: 2026-01-09 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_120000_create_sales_order_counters"
down_revision = "20260106_010000_fix_bom_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sales_order_counters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date_key", sa.String(length=8), nullable=False),
        sa.Column("last_seq", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("tenant_id", "date_key", name="uq_so_counter_tenant_date"),
    )

    # Indexes
    op.create_index(
        "ix_so_counter_tenant", "sales_order_counters", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_so_counter_date", "sales_order_counters", ["date_key"], unique=False
    )

    # Enable RLS and add tenant-isolation policy
    op.execute("ALTER TABLE sales_order_counters ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON sales_order_counters
            FOR ALL TO synkventory_app
            USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
        """
    )


def downgrade() -> None:
    op.drop_index("ix_so_counter_date", table_name="sales_order_counters")
    op.drop_index("ix_so_counter_tenant", table_name="sales_order_counters")
    op.drop_table("sales_order_counters")
