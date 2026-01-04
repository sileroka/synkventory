"""Add global attributes support

Revision ID: 20260104_000000
Revises: 20260102_000000
Create Date: 2026-01-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260104_000000"
down_revision: Union[str, None] = "20260102_000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_global column
    op.add_column(
        "category_attributes",
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Make category_id nullable for global attributes
    op.alter_column(
        "category_attributes",
        "category_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )

    # Add index for global attributes
    op.create_index(
        "ix_category_attributes_tenant_global",
        "category_attributes",
        ["tenant_id", "is_global"],
    )

    # Drop the old unique index that requires category_id
    op.drop_index(
        "ix_category_attributes_category_key", table_name="category_attributes"
    )

    # Create partial unique index for category-specific attributes
    op.execute(
        """
        CREATE UNIQUE INDEX ix_category_attributes_category_key
        ON category_attributes (category_id, key)
        WHERE category_id IS NOT NULL
    """
    )

    # Create partial unique index for global attributes
    op.execute(
        """
        CREATE UNIQUE INDEX ix_category_attributes_global_key
        ON category_attributes (tenant_id, key)
        WHERE is_global = true
    """
    )


def downgrade() -> None:
    # Drop the new indexes
    op.drop_index("ix_category_attributes_global_key", table_name="category_attributes")
    op.drop_index(
        "ix_category_attributes_category_key", table_name="category_attributes"
    )
    op.drop_index(
        "ix_category_attributes_tenant_global", table_name="category_attributes"
    )

    # Recreate the original unique index
    op.create_index(
        "ix_category_attributes_category_key",
        "category_attributes",
        ["category_id", "key"],
        unique=True,
    )

    # Make category_id not nullable again (delete global attributes first)
    op.execute("DELETE FROM category_attributes WHERE is_global = true")

    op.alter_column(
        "category_attributes",
        "category_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )

    # Drop is_global column
    op.drop_column("category_attributes", "is_global")
