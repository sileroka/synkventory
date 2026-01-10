"""
Pydantic schemas for Cycle Counts and Line Items.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.response import to_camel


# =============================================================================
# LINE ITEM SCHEMAS
# =============================================================================


class CycleCountLineItemBase(BaseModel):
    """Base schema for cycle count line items."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    item_id: UUID
    expected_quantity: int
    location_id: Optional[UUID] = None
    notes: Optional[str] = None


class CycleCountLineItemUpdate(BaseModel):
    """Update counted quantity and notes for a line item."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    counted_quantity: Optional[int] = None
    notes: Optional[str] = None


class CycleCountLineItemDetail(BaseModel):
    """Response schema for a line item including variance."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    item_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    expected_quantity: int
    counted_quantity: int
    variance: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# CYCLE COUNT SCHEMAS
# =============================================================================


class CycleCountCreate(BaseModel):
    """Create a new cycle count with optional description and line items."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    scheduled_date: date
    description: Optional[str] = None
    line_items: List[CycleCountLineItemBase] = Field(default_factory=list)


class CycleCountUpdate(BaseModel):
    """Update cycle count scheduled date or description."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    scheduled_date: Optional[date] = None
    description: Optional[str] = None


class CycleCountStatusUpdate(BaseModel):
    """Update the status of a cycle count."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str


class CycleCountDetail(BaseModel):
    """Detailed response schema including nested line items."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    scheduled_date: date
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    line_items: List[CycleCountLineItemDetail] = Field(default_factory=list)
