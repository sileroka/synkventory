"""
Add supplier_id to purchase_orders with FK and index.

Revision ID: 20260109_140000
Revises: 20260109_130000
Create Date: 2026-01-09 14:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260109_140000"
down_revision: Union[str, None] = "20260109_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add supplier_id column (nullable for backward compatibility)
    op.add_column(
        "purchase_orders",
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint to suppliers(id)
    op.create_foreign_key(
        "fk_purchase_orders_supplier_id_suppliers",
        source_table="purchase_orders",
        referent_table="suppliers",
        local_cols=["supplier_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    # Create index for supplier_id
    op.create_index(
        "idx_purchase_orders_supplier_id",
        "purchase_orders",
        ["supplier_id"],
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("idx_purchase_orders_supplier_id", table_name="purchase_orders")

    # Drop FK and column
    op.drop_constraint(
        "fk_purchase_orders_supplier_id_suppliers",
        "purchase_orders",
        type_="foreignkey",
    )
    op.drop_column("purchase_orders", "supplier_id")
