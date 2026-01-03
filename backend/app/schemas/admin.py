"""
Pydantic schemas for admin portal operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ----- Admin User Schemas -----


class AdminUserBase(BaseModel):
    """Base admin user schema."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class AdminUserCreate(AdminUserBase):
    """Schema for creating an admin user."""

    password: str = Field(..., min_length=8)
    is_super_admin: bool = False


class AdminUserUpdate(BaseModel):
    """Schema for updating an admin user."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    is_super_admin: Optional[bool] = None


class AdminUserResponse(AdminUserBase):
    """Response schema for admin user."""

    id: UUID
    is_active: bool
    is_super_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminLoginRequest(BaseModel):
    """Schema for admin login."""

    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """Response schema for admin login."""

    user: AdminUserResponse
    message: str = "Login successful"


# ----- Tenant Management Schemas -----


class TenantCreate(BaseModel):
    """Schema for creating a tenant from admin portal."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class TenantResponse(BaseModel):
    """Response schema for tenant."""

    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_count: int = 0

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    """Detailed tenant response including users."""

    pass


# ----- Tenant User Management Schemas -----


class TenantUserCreate(BaseModel):
    """Schema for creating a user within a tenant from admin portal."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    role: str = Field(default="user", pattern=r"^(viewer|user|manager|admin)$")


class TenantUserUpdate(BaseModel):
    """Schema for updating a tenant user."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern=r"^(viewer|user|manager|admin)$")
    is_active: Optional[bool] = None


class TenantUserResponse(BaseModel):
    """Response schema for tenant user."""

    id: UUID
    tenant_id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
