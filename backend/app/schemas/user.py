"""
User schemas for API requests and responses.
"""

from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class UserRole(str, Enum):
    """User roles for authorization."""

    VIEWER = "viewer"
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema with common fields."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    role: UserRole = UserRole.USER
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Full user response schema."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    role: UserRole
    is_active: bool
    is_locked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Schema for paginated list of users."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[User]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")


class RelatedUser(BaseModel):
    """Minimal user info for embedding in other responses."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    name: str
    email: str


class PasswordChange(BaseModel):
    """Schema for changing own password."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(..., min_length=8, max_length=100, alias="newPassword")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordReset(BaseModel):
    """Schema for admin resetting a user's password."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    new_password: str = Field(..., min_length=8, max_length=100, alias="newPassword")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
