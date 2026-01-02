from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class InventoryStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ON_ORDER = "on_order"
    DISCONTINUED = "discontinued"


class RelatedLocation(BaseModel):
    """Minimal location info for embedding in inventory response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class RelatedCategory(BaseModel):
    """Minimal category info for embedding in inventory response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class InventoryItemBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    sku: str
    description: Optional[str] = None
    quantity: int = 0
    reorder_point: int = 0
    unit_price: float = 0.0
    status: InventoryStatus = InventoryStatus.IN_STOCK
    category_id: Optional[str] = None
    location_id: Optional[str] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    reorder_point: Optional[int] = None
    unit_price: Optional[float] = None
    status: Optional[InventoryStatus] = None
    category_id: Optional[str] = None
    location_id: Optional[str] = None


class InventoryItem(InventoryItemBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    category: Optional[RelatedCategory] = None
    location: Optional[RelatedLocation] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
