"""
Pydantic schemas for Work Orders.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class WorkOrderStatus(str, Enum):
    """Status values for work orders."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderPriority(str, Enum):
    """Priority levels for work orders."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Nested schemas for related data
class WorkOrderItemSummary(BaseModel):
    """Summary of the item being built."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sku: str
    name: str
    totalQuantity: Optional[int] = Field(default=0, alias="total_quantity")


class WorkOrderLocationSummary(BaseModel):
    """Summary of a location."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    code: Optional[str] = None


class WorkOrderUserSummary(BaseModel):
    """Summary of a user."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    firstName: Optional[str] = Field(default=None, alias="first_name")
    lastName: Optional[str] = Field(default=None, alias="last_name")


# Request schemas
class WorkOrderCreate(BaseModel):
    """Schema for creating a new work order."""
    itemId: UUID = Field(..., alias="item_id", description="ID of the assembly item to build")
    quantityOrdered: int = Field(default=1, alias="quantity_ordered", ge=1)
    priority: WorkOrderPriority = WorkOrderPriority.NORMAL
    dueDate: Optional[datetime] = Field(default=None, alias="due_date")
    outputLocationId: Optional[UUID] = Field(default=None, alias="output_location_id")
    assignedToId: Optional[UUID] = Field(default=None, alias="assigned_to_id")
    description: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class WorkOrderUpdate(BaseModel):
    """Schema for updating a work order."""
    quantityOrdered: Optional[int] = Field(default=None, alias="quantity_ordered", ge=1)
    priority: Optional[WorkOrderPriority] = None
    dueDate: Optional[datetime] = Field(default=None, alias="due_date")
    outputLocationId: Optional[UUID] = Field(default=None, alias="output_location_id")
    assignedToId: Optional[UUID] = Field(default=None, alias="assigned_to_id")
    description: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class WorkOrderStatusUpdate(BaseModel):
    """Schema for updating work order status."""
    status: WorkOrderStatus
    notes: Optional[str] = None


class WorkOrderProgressUpdate(BaseModel):
    """Schema for recording production progress."""
    quantityCompleted: int = Field(..., alias="quantity_completed", ge=0)
    quantityScrapped: Optional[int] = Field(default=0, alias="quantity_scrapped", ge=0)
    notes: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class WorkOrderBuildRequest(BaseModel):
    """Schema for building items from a work order."""
    quantity: int = Field(..., ge=1, description="Number of assemblies to build")
    notes: Optional[str] = None


# Response schemas
class WorkOrderResponse(BaseModel):
    """Full work order response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID
    workOrderNumber: str = Field(..., alias="work_order_number")
    
    # Item info
    itemId: UUID = Field(..., alias="item_id")
    item: Optional[WorkOrderItemSummary] = None
    
    # Quantities
    quantityOrdered: int = Field(..., alias="quantity_ordered")
    quantityCompleted: int = Field(..., alias="quantity_completed")
    quantityScrapped: int = Field(..., alias="quantity_scrapped")
    quantityRemaining: Optional[int] = Field(default=None, alias="quantity_remaining")
    completionPercentage: Optional[float] = Field(default=None, alias="completion_percentage")
    
    # Status and priority
    status: WorkOrderStatus
    priority: WorkOrderPriority
    
    # Dates
    dueDate: Optional[datetime] = Field(default=None, alias="due_date")
    startDate: Optional[datetime] = Field(default=None, alias="start_date")
    completedDate: Optional[datetime] = Field(default=None, alias="completed_date")
    isOverdue: Optional[bool] = Field(default=False, alias="is_overdue")
    
    # Location and assignment
    outputLocationId: Optional[UUID] = Field(default=None, alias="output_location_id")
    outputLocation: Optional[WorkOrderLocationSummary] = Field(default=None, alias="output_location")
    assignedToId: Optional[UUID] = Field(default=None, alias="assigned_to_id")
    assignedTo: Optional[WorkOrderUserSummary] = Field(default=None, alias="assigned_to")
    
    # Notes
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Cost
    estimatedCost: Optional[Decimal] = Field(default=None, alias="estimated_cost")
    actualCost: Optional[Decimal] = Field(default=None, alias="actual_cost")
    
    # Audit
    createdAt: datetime = Field(..., alias="created_at")
    updatedAt: datetime = Field(..., alias="updated_at")
    createdBy: Optional[UUID] = Field(default=None, alias="created_by")
    updatedBy: Optional[UUID] = Field(default=None, alias="updated_by")


class WorkOrderListResponse(BaseModel):
    """Summary response for work order lists."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID
    workOrderNumber: str = Field(..., alias="work_order_number")
    
    # Item summary
    itemId: UUID = Field(..., alias="item_id")
    itemSku: Optional[str] = Field(default=None, alias="item_sku")
    itemName: Optional[str] = Field(default=None, alias="item_name")
    
    # Quantities
    quantityOrdered: int = Field(..., alias="quantity_ordered")
    quantityCompleted: int = Field(..., alias="quantity_completed")
    quantityRemaining: int = Field(default=0, alias="quantity_remaining")
    completionPercentage: float = Field(default=0.0, alias="completion_percentage")
    
    # Status and priority
    status: WorkOrderStatus
    priority: WorkOrderPriority
    
    # Dates
    dueDate: Optional[datetime] = Field(default=None, alias="due_date")
    isOverdue: bool = Field(default=False, alias="is_overdue")
    
    # Assignment
    assignedToName: Optional[str] = Field(default=None, alias="assigned_to_name")
    
    createdAt: datetime = Field(..., alias="created_at")


class WorkOrderStats(BaseModel):
    """Statistics for work orders."""
    total: int = 0
    draft: int = 0
    pending: int = 0
    inProgress: int = Field(default=0, alias="in_progress")
    onHold: int = Field(default=0, alias="on_hold")
    completed: int = 0
    cancelled: int = 0
    overdue: int = 0
    
    model_config = ConfigDict(populate_by_name=True)
