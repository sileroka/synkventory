from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, List
from datetime import datetime
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CategoryBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class Category(BaseModel):
    """Category response model - reads from ORM."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tenant_id: Optional[UUID] = None

    @field_serializer("id", "parent_id", "tenant_id")
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Serialize UUID fields to strings."""
        return str(value) if value else None


class CategoryTreeNode(Category):
    """Category with children for tree display."""

    children: List["CategoryTreeNode"] = []
