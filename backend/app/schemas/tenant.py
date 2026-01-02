"""
Tenant schemas for multi-tenancy support.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TenantBase(BaseModel):
    """Base schema for tenant data."""

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="URL-friendly unique identifier",
    )
    is_active: bool = Field(default=True, description="Whether the tenant is active")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""

    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Tenant name"
    )
    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="URL-friendly unique identifier",
    )
    is_active: Optional[bool] = Field(None, description="Whether the tenant is active")


class Tenant(TenantBase):
    """Schema for tenant response."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class RelatedTenant(BaseModel):
    """Minimal tenant schema for nested relationships."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: UUID
    name: str
    slug: str
