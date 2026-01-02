from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class RelatedLocation(BaseModel):
    """Minimal location info for embedding in response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class InventoryLocationQuantityBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    inventory_item_id: str
    location_id: str
    quantity: int = 0
    bin_location: Optional[str] = None


class InventoryLocationQuantityCreate(InventoryLocationQuantityBase):
    pass


class InventoryLocationQuantityUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    quantity: Optional[int] = None
    bin_location: Optional[str] = None


class InventoryLocationQuantity(BaseModel):
    """Response schema for inventory location quantities."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    inventory_item_id: str
    location_id: str
    quantity: int
    bin_location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested relationship
    location: Optional[RelatedLocation] = None
