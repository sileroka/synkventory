"""
Create item_lots table for serial/lot/batch tracking.

Revision ID: 20260108_000000
Revises: 20260106_010000
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260108_000000"
down_revision: Union[str, None] = "20260106_010000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create item_lots table with RLS."""

    # Create item_lots table
    op.create_table(
        "item_lots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lot_number", sa.String(100), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, default=0),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["item_id"], ["inventory_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes for common queries and multi-tenancy
    op.create_index("ix_item_lots_tenant_id", "item_lots", ["tenant_id"])
    op.create_index("ix_item_lots_item_id", "item_lots", ["item_id"])
    op.create_index("ix_item_lots_location_id", "item_lots", ["location_id"])
    op.create_index("ix_item_lots_expiration_date", "item_lots", ["expiration_date"])
    op.create_index("ix_item_lots_created_at", "item_lots", ["created_at"])

    # Unique constraint: lot number per tenant
    op.create_index(
        "ix_item_lots_tenant_lot_number",
        "item_lots",
        ["tenant_id", "lot_number"],
        unique=True,
    )

    # Multi-column indexes for efficient queries
    op.create_index(
        "ix_item_lots_tenant_item",
        "item_lots",
        ["tenant_id", "item_id"],
    )
    op.create_index(
        "ix_item_lots_tenant_location",
        "item_lots",
        ["tenant_id", "location_id"],
    )

    # Enable Row Level Security
    op.execute("ALTER TABLE item_lots ENABLE ROW LEVEL SECURITY;")

    # Create RLS policy for tenant isolation
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON item_lots
        FOR ALL TO synkventory_app
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
    """
    )

    # Admin bypass policy
    op.execute(
        """
        CREATE POLICY item_lots_admin_bypass ON item_lots
        FOR ALL TO synkventory_app
        USING (current_setting('app.is_admin', true) = 'true')
        WITH CHECK (current_setting('app.is_admin', true) = 'true');
    """
    )

    # Grant permissions to the application role
    op.execute("GRANT ALL ON item_lots TO synkventory_app;")


def downgrade() -> None:
    """Drop item_lots table and policies."""
    op.execute("DROP POLICY IF EXISTS item_lots_admin_bypass ON item_lots;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON item_lots;")
    op.drop_table("item_lots")
