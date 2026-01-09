"""
Pydantic schemas for Customers.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr
from app.schemas.response import to_camel


class CustomerBase(BaseModel):
    """Shared customer fields."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    shipping_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema for creating customers."""

    pass


class CustomerUpdate(BaseModel):
    """Schema for updating customers (all fields optional)."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    shipping_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Response schema including identifiers and audit metadata."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
