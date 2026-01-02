from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


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


class Category(CategoryBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CategoryTreeNode(Category):
    """Category with children for tree display."""

    children: List["CategoryTreeNode"] = []
