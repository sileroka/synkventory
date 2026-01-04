"""Add category_attributes table and custom_attributes to inventory_items

Revision ID: 20260104_040000
Revises: 20260104_030000
Create Date: 2026-01-04 04:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260104_040000"
down_revision: Union[str, None] = "20260104_030000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create category_attributes table and add custom_attributes to inventory_items."""

    # Create category_attributes table
    op.create_table(
        "category_attributes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column(
            "attribute_type", sa.String(20), nullable=False, server_default="text"
        ),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("options", sa.String(1000), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("default_value", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )

    # Create indexes
    op.create_index(
        "ix_category_attributes_tenant_id",
        "category_attributes",
        ["tenant_id"],
    )
    op.create_index(
        "ix_category_attributes_category_id",
        "category_attributes",
        ["category_id"],
    )
    op.create_index(
        "ix_category_attributes_tenant_category",
        "category_attributes",
        ["tenant_id", "category_id"],
    )
    op.create_index(
        "ix_category_attributes_category_key",
        "category_attributes",
        ["category_id", "key"],
        unique=True,
    )

    # Grant permissions to app role
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON category_attributes TO synkventory_app"
    )

    # Enable RLS
    op.execute("ALTER TABLE category_attributes ENABLE ROW LEVEL SECURITY")

    # Tenant isolation policy
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON category_attributes
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )

    # Admin bypass policy (uses app.is_admin setting, not a role)
    op.execute(
        """
        CREATE POLICY category_attributes_admin_bypass ON category_attributes
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )

    # Add custom_attributes JSONB column to inventory_items
    op.add_column(
        "inventory_items",
        sa.Column("custom_attributes", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    """Remove custom_attributes and category_attributes table."""

    # Remove custom_attributes column from inventory_items
    op.drop_column("inventory_items", "custom_attributes")

    # Drop policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON category_attributes")
    op.execute(
        "DROP POLICY IF EXISTS category_attributes_admin_bypass ON category_attributes"
    )

    # Drop indexes
    op.drop_index(
        "ix_category_attributes_category_key", table_name="category_attributes"
    )
    op.drop_index(
        "ix_category_attributes_tenant_category", table_name="category_attributes"
    )
    op.drop_index(
        "ix_category_attributes_category_id", table_name="category_attributes"
    )
    op.drop_index("ix_category_attributes_tenant_id", table_name="category_attributes")

    # Drop table
    op.drop_table("category_attributes")
