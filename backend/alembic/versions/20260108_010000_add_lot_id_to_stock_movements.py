"""
Add lot_id to stock_movements for lot traceability.

Revision ID: 20260108_010000
Revises: 20260108_000000
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260108_010000"
down_revision: Union[str, None] = "20260108_000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add lot_id column to stock_movements table."""

    # Add lot_id column with foreign key to item_lots
    op.add_column(
        "stock_movements",
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_stock_movements_lot_id",
        "stock_movements",
        "item_lots",
        ["lot_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for efficient queries
    op.create_index("ix_stock_movements_lot_id", "stock_movements", ["lot_id"])


def downgrade() -> None:
    """Remove lot_id column from stock_movements table."""
    op.drop_index("ix_stock_movements_lot_id", table_name="stock_movements")
    op.drop_constraint(
        "fk_stock_movements_lot_id",
        "stock_movements",
        type_="foreignkey",
    )
    op.drop_column("stock_movements", "lot_id")
