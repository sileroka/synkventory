from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InventoryItemBase(BaseModel):
    name: str
    sku: str
    description: Optional[str] = None
    quantity: int = 0
    unit_price: float = 0.0
    category: Optional[str] = None
    location: Optional[str] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    category: Optional[str] = None
    location: Optional[str] = None


class InventoryItem(InventoryItemBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
