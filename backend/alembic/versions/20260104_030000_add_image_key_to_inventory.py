"""Add image_key to inventory_items

Revision ID: 20260104_030000
Revises: 0008
Create Date: 2026-01-04 03:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260104_030000"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add image_key column to inventory_items table."""
    op.add_column(
        "inventory_items", sa.Column("image_key", sa.String(512), nullable=True)
    )


def downgrade() -> None:
    """Remove image_key column from inventory_items table."""
    op.drop_column("inventory_items", "image_key")
