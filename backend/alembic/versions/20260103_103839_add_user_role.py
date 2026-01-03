"""Add role column to users table

Revision ID: 20260103_103839
Revises: 20260102_000000
Create Date: 2026-01-03 10:38:39

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260103_103839"
down_revision: Union[str, None] = "20260102_000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column with default value for existing users
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(50),
            nullable=False,
            server_default="user",
        ),
    )

    # Update system user to be admin
    op.execute(
        """
        UPDATE users 
        SET role = 'admin' 
        WHERE id = '00000000-0000-0000-0000-000000000001'
        """
    )


def downgrade() -> None:
    op.drop_column("users", "role")
