"""
Tenant model for multi-tenancy support.
This enables SaaS multi-tenancy where each tenant has isolated data.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


# Default tenant UUID - used for single-tenant deployments and migrations
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class Tenant(Base):
    """
    Tenant model for multi-tenancy support.

    Each tenant represents an isolated organization/company using Synkventory.
    All data (inventory, locations, categories, etc.) is scoped to a tenant.

    NOTE: Tenant filtering middleware will be implemented in a future phase.
    This model provides the database structure for multi-tenancy.
    """

    __tablename__ = "tenants"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"
