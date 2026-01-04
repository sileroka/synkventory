"""
Audit log schemas for API requests and responses.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class AuditActionEnum(str, Enum):
    """Audit action types."""

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


class EntityTypeEnum(str, Enum):
    """Entity types for audit logging."""

    USER = "USER"
    TENANT = "TENANT"
    INVENTORY_ITEM = "INVENTORY_ITEM"
    CATEGORY = "CATEGORY"
    LOCATION = "LOCATION"
    STOCK_MOVEMENT = "STOCK_MOVEMENT"
    REPORT = "REPORT"
    SYSTEM = "SYSTEM"


class AuditLogBase(BaseModel):
    """Base audit log schema."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry (internal use)."""

    tenant_id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLog(AuditLogBase):
    """Full audit log response schema."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AuditLogSummary(BaseModel):
    """Condensed audit log for lists."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    action: str
    entity_type: str
    entity_name: Optional[str] = None
    user_email: Optional[str] = None
    created_at: datetime


class AuditLogFilters(BaseModel):
    """Filters for querying audit logs."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    user_id: Optional[UUID] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
