"""
Create item_revisions table for inventory item version control

Revision ID: 20260104_070000
Revises: 20260104_060000
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260104_070000"
down_revision: Union[str, None] = "20260104_060000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create item_revisions table."""
    op.create_table(
        "item_revisions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Revision metadata
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("revision_type", sa.String(50), nullable=False),
        # Snapshot of inventory item fields
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reorder_point", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("image_key", sa.String(512), nullable=True),
        sa.Column("custom_attributes", postgresql.JSONB, nullable=True),
        # Change details
        sa.Column("changes", postgresql.JSONB, nullable=True),
        sa.Column("change_summary", sa.String(500), nullable=True),
        # Who made the change
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        # When
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"], ["inventory_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes for common queries
    op.create_index("ix_item_revisions_tenant_id", "item_revisions", ["tenant_id"])
    op.create_index(
        "ix_item_revisions_inventory_item_id", "item_revisions", ["inventory_item_id"]
    )
    op.create_index(
        "ix_item_revisions_revision_type", "item_revisions", ["revision_type"]
    )
    op.create_index("ix_item_revisions_created_by", "item_revisions", ["created_by"])
    op.create_index("ix_item_revisions_created_at", "item_revisions", ["created_at"])
    op.create_index(
        "ix_item_revisions_item_revision",
        "item_revisions",
        ["inventory_item_id", "revision_number"],
        unique=True,
    )
    op.create_index(
        "ix_item_revisions_tenant_item",
        "item_revisions",
        ["tenant_id", "inventory_item_id"],
    )
    op.create_index(
        "ix_item_revisions_tenant_created",
        "item_revisions",
        ["tenant_id", "created_at"],
    )

    # Enable RLS
    op.execute("ALTER TABLE item_revisions ENABLE ROW LEVEL SECURITY")

    # Tenant isolation policy (with NULLIF to handle empty strings)
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON item_revisions
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )

    # Admin bypass policy
    op.execute(
        """
        CREATE POLICY item_revisions_admin_bypass ON item_revisions
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )

    # Grant permissions to app user
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON item_revisions TO synkventory_app"
    )


def downgrade() -> None:
    """Drop item_revisions table."""
    op.execute("DROP POLICY IF EXISTS item_revisions_admin_bypass ON item_revisions")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON item_revisions")
    op.drop_table("item_revisions")
