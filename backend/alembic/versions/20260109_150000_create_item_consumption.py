"""
Create item_consumption table to record historical consumption.

Revision ID: 20260109_150000
Revises: 20260109_140000
Create Date: 2026-01-09 15:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260109_150000"
down_revision: Union[str, None] = "20260109_140000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for consumption source
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consumption_source') THEN
                CREATE TYPE consumption_source AS ENUM (
                    'sales_order',
                    'work_order',
                    'adjustment',
                    'transfer',
                    'other'
                );
            END IF;
        END $$;
        """
    )

    # Create table
    op.create_table(
        "item_consumption",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM(
                "sales_order",
                "work_order",
                "adjustment",
                "transfer",
                "other",
                name="consumption_source",
                create_type=False,
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes
    op.create_index("idx_item_consumption_tenant_id", "item_consumption", ["tenant_id"])
    op.create_index("idx_item_consumption_item_id", "item_consumption", ["item_id"])
    op.create_index("idx_item_consumption_date", "item_consumption", ["date"])
    op.create_index("idx_item_consumption_source", "item_consumption", ["source"])

    # Enable RLS and add policy
    op.execute("ALTER TABLE item_consumption ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON item_consumption
            FOR ALL TO synkventory_app
            USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
        """
    )
    op.execute(
        """
        CREATE POLICY admin_bypass_policy ON item_consumption
            FOR ALL TO synkventory_admin
            USING (true)
            WITH CHECK (true);
        """
    )

    # Grants
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON item_consumption TO synkventory_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON item_consumption TO synkventory_admin;")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_bypass_policy ON item_consumption;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON item_consumption;")
    op.drop_table("item_consumption")
    op.execute("DROP TYPE IF EXISTS consumption_source;")
