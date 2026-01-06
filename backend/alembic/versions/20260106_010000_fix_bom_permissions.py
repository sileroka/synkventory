"""
Fix missing GRANT permissions for bill_of_materials table.

Revision ID: 20260106_010000
Revises: 20260104_100000
Create Date: 2026-01-06
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260106_010000"
down_revision: Union[str, None] = "20260104_100000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing GRANT permissions for bill_of_materials table."""
    # Grant permissions to synkventory_app role (was missing in original migration)
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON bill_of_materials TO synkventory_app;"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON bill_of_materials TO synkventory_admin;"
    )


def downgrade() -> None:
    """Revoke permissions (not typically done but included for completeness)."""
    op.execute("REVOKE ALL ON bill_of_materials FROM synkventory_app;")
    op.execute("REVOKE ALL ON bill_of_materials FROM synkventory_admin;")
