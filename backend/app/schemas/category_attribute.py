"""
Category attribute schemas for API requests and responses.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class AttributeType(str, Enum):
    """Supported attribute types."""

    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"


class CategoryAttributeBase(BaseModel):
    """Base schema for category attributes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    attribute_type: AttributeType = AttributeType.TEXT
    description: Optional[str] = Field(None, max_length=500)
    options: Optional[str] = Field(None, max_length=1000)
    is_required: bool = False
    default_value: Optional[str] = Field(None, max_length=500)
    display_order: int = 0

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Ensure key is lowercase and uses underscores."""
        return v.lower().replace("-", "_")


class CategoryAttributeCreate(CategoryAttributeBase):
    """Schema for creating a category attribute."""

    category_id: Optional[str] = None
    is_global: bool = False


class CategoryAttributeUpdate(BaseModel):
    """Schema for updating a category attribute."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    options: Optional[str] = Field(None, max_length=1000)
    is_required: Optional[bool] = None
    default_value: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryAttribute(CategoryAttributeBase):
    """Schema for category attribute response."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    category_id: Optional[str] = None
    is_global: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("id", "category_id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        """Convert UUID to string."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v


class CategoryAttributeReorder(BaseModel):
    """Schema for reordering attributes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    attribute_ids: List[str] = Field(..., description="Ordered list of attribute IDs")
