"""
Admin User model for the admin portal.
These are super-admin users who can manage tenants and tenant users.
Completely separate from tenant-scoped users.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


class AdminUser(Base):
    """
    Admin user model for the admin portal at admin.synkventory.com.

    These users are NOT scoped to any tenant - they have cross-tenant access
    to manage tenants and their users.
    """

    __tablename__ = "admin_users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_super_admin = Column(
        Boolean, default=False, nullable=False
    )  # Full system access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AdminUser {self.email}>"
