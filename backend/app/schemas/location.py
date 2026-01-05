from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


# Location type constants
LocationTypeEnum = Literal["warehouse", "row", "bay", "level", "position"]


class LocationBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    code: str
    location_type: LocationTypeEnum = "warehouse"
    parent_id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    barcode: Optional[str] = None
    capacity: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: Optional[str] = None
    code: Optional[str] = None
    location_type: Optional[LocationTypeEnum] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    barcode: Optional[str] = None
    capacity: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class Location(BaseModel):
    """Location response model with hierarchy support."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    name: str
    code: str
    location_type: str
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    address: Optional[str] = None
    barcode: Optional[str] = None
    capacity: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("id", "parent_id")
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Serialize UUID fields to strings."""
        return str(value) if value else None


class LocationTreeNode(Location):
    """Location with children for tree display."""

    children: List["LocationTreeNode"] = []
    full_path: Optional[str] = None


class LocationTypeInfo(BaseModel):
    """Information about a location type."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: str
    display_name: str
    allowed_child_type: Optional[str] = None
