from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class RelatedInventoryItem(BaseModel):
    """Minimal inventory item info for embedding in lot response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    name: str
    sku: str


class RelatedLocation(BaseModel):
    """Minimal location info for embedding in lot response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: UUID
    name: str
    code: str


class ItemLotBase(BaseModel):
    """Base schema for lot operations."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    lot_number: str
    serial_number: Optional[str] = None
    quantity: int
    expiration_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    location_id: Optional[UUID] = None


class ItemLotCreate(ItemLotBase):
    """Schema for creating a new lot."""

    lot_number: str  # Required
    quantity: int  # Required

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("lot_number")
    @classmethod
    def lot_number_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Lot number cannot be empty")
        return v.strip()


class ItemLotUpdate(BaseModel):
    """Schema for updating a lot with all fields optional."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    quantity: Optional[int] = None
    expiration_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    location_id: Optional[UUID] = None

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("lot_number")
    @classmethod
    def lot_number_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Lot number cannot be empty")
        return v.strip() if v else None


class ItemLotResponse(BaseModel):
    """Response schema for lot with full details."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    item_id: UUID
    lot_number: str
    serial_number: Optional[str] = None
    quantity: int
    expiration_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    location_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Nested relationships
    item: Optional[RelatedInventoryItem] = None
    location: Optional[RelatedLocation] = None
