"""
User model for authentication and audit tracking.
"""

import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


# System user UUID - used for migrations, seeds, and system operations
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class UserRole(str, Enum):
    """User roles for authorization."""
    VIEWER = "viewer"      # Can only view data
    USER = "user"          # Can view and edit inventory
    MANAGER = "manager"    # Can manage users and settings
    ADMIN = "admin"        # Full access including tenant settings


class User(Base):
    """
    User model for authentication.

    Users are scoped to tenants - the same email can exist in different tenants.
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.USER.value)
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", backref="users")

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has one of the specified roles."""
        return self.role in [r.value for r in roles]

    def is_manager_or_above(self) -> bool:
        """Check if user is manager or admin."""
        return self.role in [UserRole.MANAGER.value, UserRole.ADMIN.value]

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN.value
