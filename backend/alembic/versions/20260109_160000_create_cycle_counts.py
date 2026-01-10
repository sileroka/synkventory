"""
Create cycle_counts and cycle_count_line_items tables for physical inventory cycle counts.

Revision ID: 20260109_160000
Revises: 20260109_150000
Create Date: 2026-01-09 16:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260109_160000"
down_revision: Union[str, None] = "20260109_150000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cycle count tables, indices, and RLS policies."""

    # Create enum type for cycle count status
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cycle_count_status') THEN
                CREATE TYPE cycle_count_status AS ENUM (
                    'scheduled',
                    'in_progress',
                    'completed',
                    'approved',
                    'cancelled'
                );
            END IF;
        END $$;
        """
    )

    # cycle_counts table
    op.create_table(
        "cycle_counts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "scheduled",
                "in_progress",
                "completed",
                "approved",
                "cancelled",
                name="cycle_count_status",
                create_type=False,
            ),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("description", sa.Text, nullable=True),
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

    # Indices for cycle_counts
    op.create_index("ix_cycle_counts_tenant_id", "cycle_counts", ["tenant_id"])  # general tenant lookup
    op.create_index(
        "ix_cycle_counts_tenant_scheduled_date",
        "cycle_counts",
        ["tenant_id", "scheduled_date"],
    )
    op.create_index("ix_cycle_counts_status", "cycle_counts", ["status"])  # status filter

    # cycle_count_line_items table
    op.create_table(
        "cycle_count_line_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_count_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("counted_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
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
        sa.ForeignKeyConstraint(["cycle_count_id"], ["cycle_counts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Indices for line items
    op.create_index("ix_cycle_count_line_items_tenant_id", "cycle_count_line_items", ["tenant_id"])  # tenant lookup
    op.create_index(
        "ix_cycle_count_line_items_cycle_item",
        "cycle_count_line_items",
        ["cycle_count_id", "item_id"],
    )
    op.create_index("ix_cycle_count_line_items_location_id", "cycle_count_line_items", ["location_id"])  # location filter

    # Enable RLS and add policies
    op.execute("ALTER TABLE cycle_counts ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON cycle_counts
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )
    op.execute(
        """
        CREATE POLICY cycle_counts_admin_bypass ON cycle_counts
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_counts TO synkventory_app;")

    op.execute("ALTER TABLE cycle_count_line_items ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON cycle_count_line_items
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )
    op.execute(
        """
        CREATE POLICY cycle_count_line_items_admin_bypass ON cycle_count_line_items
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_count_line_items TO synkventory_app;")


def downgrade() -> None:
    # Drop RLS policies and tables
    op.execute("DROP POLICY IF EXISTS cycle_count_line_items_admin_bypass ON cycle_count_line_items;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON cycle_count_line_items;")
    op.execute("DROP POLICY IF EXISTS cycle_counts_admin_bypass ON cycle_counts;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON cycle_counts;")

    op.drop_table("cycle_count_line_items")
    op.drop_table("cycle_counts")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS cycle_count_status;")
