"""
AuditLog model for tracking all system activities.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class AuditLog(Base):
    """
    Audit log entry for tracking user actions and system events.

    Tracks:
    - User authentication (login/logout)
    - CRUD operations on all entities
    - Stock movements and inventory changes
    - Administrative actions
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Who performed the action
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)

    # What action was performed
    action = Column(String(50), nullable=False, index=True)

    # What entity was affected
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_name = Column(String(255), nullable=True)

    # Details of the change
    changes = Column(JSONB, nullable=True)  # {field: {old: x, new: y}}
    extra_data = Column(JSONB, nullable=True)  # Additional context

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    tenant = relationship("Tenant", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type} by {self.user_email}>"


# Action types
class AuditAction:
    """Standard audit action types."""

    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"

    # CRUD operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Inventory-specific
    STOCK_RECEIVE = "STOCK_RECEIVE"
    STOCK_SHIP = "STOCK_SHIP"
    STOCK_TRANSFER = "STOCK_TRANSFER"
    STOCK_ADJUST = "STOCK_ADJUST"
    STOCK_COUNT = "STOCK_COUNT"

    # Bulk operations
    BULK_DELETE = "BULK_DELETE"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_IMPORT = "BULK_IMPORT"
    BULK_EXPORT = "BULK_EXPORT"

    # User management
    USER_ACTIVATE = "USER_ACTIVATE"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    USER_LOCK = "USER_LOCK"
    USER_UNLOCK = "USER_UNLOCK"

    # Navigation/Activity
    PAGE_VIEW = "PAGE_VIEW"


# Entity types
class EntityType:
    """Standard entity types for audit logging."""

    USER = "USER"
    TENANT = "TENANT"
    INVENTORY_ITEM = "INVENTORY_ITEM"
    ITEM_REVISION = "ITEM_REVISION"
    CATEGORY = "CATEGORY"
    LOCATION = "LOCATION"
    STOCK_MOVEMENT = "STOCK_MOVEMENT"
    BILL_OF_MATERIAL = "BILL_OF_MATERIAL"
    WORK_ORDER = "WORK_ORDER"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    SUPPLIER = "SUPPLIER"
    REPORT = "REPORT"
    SYSTEM = "SYSTEM"
