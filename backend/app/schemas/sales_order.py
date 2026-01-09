"""
Pydantic schemas for Sales Orders.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerResponse


# =============================================================================
# LINE ITEM SCHEMAS
# =============================================================================


class SalesOrderLineItemBase(BaseModel):
    """Base schema for sales order line items."""

    item_id: Optional[UUID] = None
    quantity_ordered: int = Field(ge=1, default=1)
    unit_price: Decimal = Field(ge=0, default=Decimal("0"))
    notes: Optional[str] = None


class SalesOrderLineItemCreate(SalesOrderLineItemBase):
    """Schema for creating a sales order line item."""

    pass


class SalesOrderLineItemUpdate(BaseModel):
    """Schema for updating a sales order line item."""

    item_id: Optional[UUID] = None
    quantity_ordered: Optional[int] = Field(None, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class SalesOrderLineItemResponse(SalesOrderLineItemBase):
    """Response schema for sales order line item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sales_order_id: UUID
    quantity_shipped: int
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    # Computed
    quantity_remaining: int = 0


class SalesOrderLineItemWithItem(SalesOrderLineItemResponse):
    """Line item response including item details for list/detail views."""

    item_name: Optional[str] = None
    item_sku: Optional[str] = None
    current_quantity: Optional[int] = None
    reorder_point: Optional[int] = None


# =============================================================================
# SALES ORDER SCHEMAS
# =============================================================================


class SalesOrderBase(BaseModel):
    """Base schema for sales orders."""

    customer_id: Optional[UUID] = None
    priority: str = "normal"
    order_date: Optional[datetime] = None
    expected_ship_date: Optional[datetime] = None
    notes: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    """Schema for creating a sales order."""

    line_items: List[SalesOrderLineItemCreate] = Field(default_factory=list)


class SalesOrderUpdate(BaseModel):
    """Schema for updating a sales order."""

    customer_id: Optional[UUID] = None
    priority: Optional[str] = None
    order_date: Optional[datetime] = None
    expected_ship_date: Optional[datetime] = None
    notes: Optional[str] = None
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)


class SalesOrderStatusUpdate(BaseModel):
    """Schema for updating sales order status."""

    status: str
    notes: Optional[str] = None


class SalesOrderResponse(SalesOrderBase):
    """Response schema for sales order."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_number: str
    status: str
    shipped_date: Optional[datetime]
    cancelled_date: Optional[datetime]
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    # Nested customer details (if linked)
    customer: Optional[CustomerResponse] = None


class SalesOrderListItem(BaseModel):
    """Simplified schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    customer_id: Optional[UUID] = None
    status: str
    priority: str
    total_amount: Decimal
    order_date: Optional[datetime]
    expected_ship_date: Optional[datetime]
    shipped_date: Optional[datetime]
    created_at: datetime

    # Counts
    item_count: int = 0
    items_shipped: int = 0

    # Customer
    customer: Optional[CustomerResponse] = None

    # Computed
    is_overdue: bool = False


class SalesOrderDetail(SalesOrderResponse):
    """Detailed schema with nested data and computed totals."""

    line_items: List[SalesOrderLineItemWithItem] = []
    customer_name: Optional[str] = None
    is_overdue: bool = False
