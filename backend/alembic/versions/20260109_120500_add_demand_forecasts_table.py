"""
Add demand_forecasts table with RLS

Revision ID: 20260109_120500_add_demand_forecasts_table
Revises: 20260109_120000
Create Date: 2026-01-09 12:05:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_120500_add_demand_forecasts_table"
down_revision = "20260109_120000"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demand_forecasts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=False),
        sa.Column("confidence_low", sa.Float(), nullable=True),
        sa.Column("confidence_high", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Indexes
    op.create_index(
        "ix_demand_forecasts_tenant_item_date",
        "demand_forecasts",
        ["tenant_id", "item_id", "forecast_date"],
        unique=False,
    )

    # Enable RLS and add tenant isolation/admin bypass policies
    op.execute("ALTER TABLE demand_forecasts ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON demand_forecasts
            FOR ALL TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
        """
    )
    op.execute(
        """
        CREATE POLICY demand_forecasts_admin_bypass ON demand_forecasts
            FOR ALL TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true');
        """
    )

    # Grant permissions to app role
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON demand_forecasts TO synkventory_app;")


def downgrade():
    op.execute("DROP POLICY IF EXISTS demand_forecasts_admin_bypass ON demand_forecasts;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON demand_forecasts;")
    op.drop_index("ix_demand_forecasts_tenant_item_date", table_name="demand_forecasts")
    op.drop_table("demand_forecasts")
