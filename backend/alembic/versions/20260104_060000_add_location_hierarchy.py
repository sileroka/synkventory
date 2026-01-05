"""Add location hierarchy support (warehouse, row, bay, level, position)

Revision ID: 20260104_060000
Revises: 20260104_050000
Create Date: 2026-01-04 06:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260104_060000"
down_revision: Union[str, None] = "20260104_050000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add hierarchy columns to locations table."""

    # Add location_type column
    op.add_column(
        "locations",
        sa.Column(
            "location_type",
            sa.String(20),
            nullable=False,
            server_default="warehouse",
        ),
    )

    # Add parent_id column for hierarchy
    op.add_column(
        "locations",
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # Add description column
    op.add_column(
        "locations",
        sa.Column(
            "description",
            sa.String(500),
            nullable=True,
        ),
    )

    # Add capacity column for storage capacity
    op.add_column(
        "locations",
        sa.Column(
            "capacity",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Add barcode column for location identification
    op.add_column(
        "locations",
        sa.Column(
            "barcode",
            sa.String(100),
            nullable=True,
        ),
    )

    # Add sort_order for ordering within parent
    op.add_column(
        "locations",
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Create index for parent_id lookups
    op.create_index(
        "ix_locations_parent_id",
        "locations",
        ["parent_id"],
    )

    # Create index for location_type filtering
    op.create_index(
        "ix_locations_location_type",
        "locations",
        ["location_type"],
    )

    # Create index for tenant + parent_id queries
    op.create_index(
        "ix_locations_tenant_parent",
        "locations",
        ["tenant_id", "parent_id"],
    )

    # Create unique index for barcode per tenant
    op.create_index(
        "ix_locations_tenant_barcode",
        "locations",
        ["tenant_id", "barcode"],
        unique=True,
        postgresql_where=sa.text("barcode IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove hierarchy columns from locations table."""

    # Drop indexes
    op.drop_index("ix_locations_tenant_barcode", table_name="locations")
    op.drop_index("ix_locations_tenant_parent", table_name="locations")
    op.drop_index("ix_locations_location_type", table_name="locations")
    op.drop_index("ix_locations_parent_id", table_name="locations")

    # Drop columns
    op.drop_column("locations", "sort_order")
    op.drop_column("locations", "barcode")
    op.drop_column("locations", "capacity")
    op.drop_column("locations", "description")
    op.drop_column("locations", "parent_id")
    op.drop_column("locations", "location_type")
