"""
Create audit_logs table for comprehensive activity tracking

Revision ID: 0008
Revises: 0007
Create Date: 2026-01-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_name", sa.String(255), nullable=True),
        sa.Column("changes", postgresql.JSONB, nullable=True),
        sa.Column("extra_data", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    # Indexes for common queries
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index(
        "ix_audit_logs_tenant_created",
        "audit_logs",
        ["tenant_id", "created_at"],
    )

    # Enable RLS
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")

    # Tenant isolation policy (with NULLIF to handle empty strings)
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON audit_logs
            FOR ALL
            TO synkventory_app
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)
        """
    )

    # Admin bypass policy
    op.execute(
        """
        CREATE POLICY audit_logs_admin_bypass ON audit_logs
            FOR ALL
            TO synkventory_app
            USING (current_setting('app.is_admin', true) = 'true')
            WITH CHECK (current_setting('app.is_admin', true) = 'true')
        """
    )

    # Grant permissions to app user
    op.execute("GRANT SELECT, INSERT ON audit_logs TO synkventory_app")


def downgrade() -> None:
    """Drop audit_logs table."""
    op.execute("DROP POLICY IF EXISTS audit_logs_admin_bypass ON audit_logs")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON audit_logs")
    op.drop_table("audit_logs")
