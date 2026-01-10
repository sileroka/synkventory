"""
Add barcode fields to inventory_items and unique index on (tenant_id, barcode).

Revision ID: 20260109_130000
Revises: 20260109_120000
Create Date: 2026-01-09 13:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260109_130000"
down_revision: Union[str, None] = "20260109_120500_add_demand_forecasts_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns
    op.add_column(
        "inventory_items",
        sa.Column("barcode", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "inventory_items",
        sa.Column("barcode_image_key", sa.String(length=512), nullable=True),
    )

    # Create unique composite index for tenant+barcode
    op.create_index(
        "uq_inventory_items_tenant_barcode",
        "inventory_items",
        ["tenant_id", "barcode"],
        unique=True,
        postgresql_concurrently=False,
    )


def downgrade() -> None:
    # Drop unique index
    op.drop_index("uq_inventory_items_tenant_barcode", table_name="inventory_items")

    # Drop columns
    op.drop_column("inventory_items", "barcode_image_key")
    op.drop_column("inventory_items", "barcode")
