"""
Pydantic schemas for Purchase Orders.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.supplier import SupplierResponse


# =============================================================================
# LINE ITEM SCHEMAS
# =============================================================================


class PurchaseOrderLineItemBase(BaseModel):
    """Base schema for PO line items."""

    item_id: UUID
    quantity_ordered: int = Field(ge=1, default=1)
    unit_price: Decimal = Field(ge=0, default=Decimal("0"))
    notes: Optional[str] = None


class PurchaseOrderLineItemCreate(PurchaseOrderLineItemBase):
    """Schema for creating a PO line item."""

    pass


class PurchaseOrderLineItemUpdate(BaseModel):
    """Schema for updating a PO line item."""

    quantity_ordered: Optional[int] = Field(None, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class PurchaseOrderLineItemReceive(BaseModel):
    """Schema for receiving items on a line."""

    quantity_received: int = Field(ge=0)
    notes: Optional[str] = None


class PurchaseOrderLineItemResponse(PurchaseOrderLineItemBase):
    """Response schema for PO line item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    quantity_received: int
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    # Computed
    quantity_remaining: int = 0


class PurchaseOrderLineItemWithItem(PurchaseOrderLineItemResponse):
    """Line item with nested item details."""

    item_name: Optional[str] = None
    item_sku: Optional[str] = None
    current_quantity: Optional[int] = None
    reorder_point: Optional[int] = None


# =============================================================================
# PURCHASE ORDER SCHEMAS
# =============================================================================


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    priority: str = "normal"
    expected_date: Optional[datetime] = None
    receiving_location_id: Optional[UUID] = None
    notes: Optional[str] = None
    external_reference: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    supplier_id: Optional[UUID] = None
    line_items: List[PurchaseOrderLineItemCreate] = Field(default_factory=list)
    requested_by_id: Optional[UUID] = None


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""

    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    priority: Optional[str] = None
    expected_date: Optional[datetime] = None
    receiving_location_id: Optional[UUID] = None
    notes: Optional[str] = None
    external_reference: Optional[str] = None
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)


class PurchaseOrderStatusUpdate(BaseModel):
    """Schema for updating PO status."""

    status: str
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Response schema for purchase order."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    po_number: str
    supplier_id: Optional[UUID] = None
    status: str
    order_date: Optional[datetime]
    received_date: Optional[datetime]
    requested_by_id: Optional[UUID]
    approved_by_id: Optional[UUID]
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    auto_generated: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    # Nested supplier details (if linked)
    supplier: Optional[SupplierResponse] = None


class PurchaseOrderListItem(BaseModel):
    """Simplified schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str]
    status: str
    priority: str
    total_amount: Decimal
    order_date: Optional[datetime]
    expected_date: Optional[datetime]
    received_date: Optional[datetime]
    auto_generated: bool
    created_at: datetime

    # Counts
    item_count: int = 0
    items_received: int = 0

    # User info
    requested_by_name: Optional[str] = None

    # Supplier
    supplier: Optional[SupplierResponse] = None

    # Computed
    is_overdue: bool = False


class PurchaseOrderDetail(PurchaseOrderResponse):
    """Detailed schema with nested data."""

    line_items: List[PurchaseOrderLineItemWithItem] = []
    requested_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    receiving_location_name: Optional[str] = None
    is_overdue: bool = False


# =============================================================================
# LOW STOCK SCHEMAS
# =============================================================================


class LowStockItem(BaseModel):
    """Schema for low stock item suggestions."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sku: str
    current_quantity: int
    reorder_point: int
    unit_price: float
    shortage: int  # How many below reorder point
    suggested_quantity: int  # Suggested order quantity


class LowStockSuggestion(BaseModel):
    """Schema for auto-generated PO suggestion."""

    items: List[LowStockItem]
    total_items: int
    estimated_total: Decimal


# =============================================================================
# STATS SCHEMAS
# =============================================================================


class PurchaseOrderStats(BaseModel):
    """Statistics for purchase orders."""

    total: int = 0
    draft: int = 0
    pending_approval: int = 0
    approved: int = 0
    ordered: int = 0
    partially_received: int = 0
    received: int = 0
    cancelled: int = 0
    overdue: int = 0
    total_value_pending: Decimal = Decimal("0")


# =============================================================================
# RECEIVE SCHEMAS
# =============================================================================


class ReceivedLot(BaseModel):
    """Schema for receiving items as a lot/batch."""

    lot_number: str
    serial_number: Optional[str] = None
    quantity: int = Field(ge=1)
    expiration_date: Optional[datetime] = None
    manufacture_date: Optional[datetime] = None


class ReceiveLineItem(BaseModel):
    """Schema for receiving a specific line item."""

    line_item_id: UUID
    quantity_received: int = Field(ge=0)
    lots: Optional[List[ReceivedLot]] = None


class ReceiveItemsRequest(BaseModel):
    """Schema for receiving multiple items at once."""

    items: List[ReceiveLineItem]
    notes: Optional[str] = None
    received_date: Optional[datetime] = None
