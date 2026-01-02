"""
User model for authentication and audit tracking.
This is a placeholder for future SynkAuth integration.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


# System user UUID - used for migrations, seeds, and system operations
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class User(Base):
    """
    User model for tracking who created/modified records.

    NOTE: This is a placeholder model. Full authentication will be
    handled by SynkAuth integration in a future phase. For now, this
    model supports:
    - Audit trail (created_by/updated_by foreign keys)
    - System user for automated operations
    - Basic user info storage
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User {self.email}>"
