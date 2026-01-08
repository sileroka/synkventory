from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class MovementType(str, Enum):
    RECEIVE = "receive"
    SHIP = "ship"
    TRANSFER = "transfer"
    ADJUST = "adjust"
    COUNT = "count"


class RelatedInventoryItem(BaseModel):
    """Minimal inventory item info for embedding in movement response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    sku: str


class RelatedLocation(BaseModel):
    """Minimal location info for embedding in movement response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class StockMovementBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    inventory_item_id: str
    movement_type: MovementType
    quantity: int
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    lot_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    @field_validator("quantity")
    @classmethod
    def quantity_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Quantity cannot be zero")
        return v


class StockMovement(BaseModel):
    """Response schema for stock movements."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    inventory_item_id: str
    movement_type: MovementType
    quantity: int
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    lot_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Nested relationships
    inventory_item: Optional[RelatedInventoryItem] = None
    from_location: Optional[RelatedLocation] = None
    to_location: Optional[RelatedLocation] = None
