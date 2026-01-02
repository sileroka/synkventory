"""
User schemas for API responses.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class UserBase(BaseModel):
    """Base user schema with common fields."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Full user response schema."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RelatedUser(BaseModel):
    """Minimal user info for embedding in other responses."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    email: str
