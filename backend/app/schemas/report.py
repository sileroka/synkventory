"""
Schemas for report endpoints.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ValuationItemCategory(BaseModel):
    """Category info for valuation item."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class ValuationItemLocation(BaseModel):
    """Location info for valuation item."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class ValuationItem(BaseModel):
    """Individual item in valuation report."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    sku: str
    name: str
    quantity: int
    unit_price: float
    total_value: float
    category: Optional[ValuationItemCategory] = None
    location: Optional[ValuationItemLocation] = None


class CategoryValuationSummary(BaseModel):
    """Valuation summary grouped by category."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category_id: Optional[str] = None
    category_name: str
    category_code: Optional[str] = None
    item_count: int
    total_units: int
    total_value: float


class LocationValuationSummary(BaseModel):
    """Valuation summary grouped by location."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    location_id: Optional[str] = None
    location_name: str
    location_code: Optional[str] = None
    item_count: int
    total_units: int
    total_value: float


class InventoryValuationReport(BaseModel):
    """Complete inventory valuation report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # Summary totals
    total_items: int
    total_units: int
    total_value: float

    # Item-level detail
    items: List[ValuationItem]

    # Grouped summaries
    by_category: List[CategoryValuationSummary]
    by_location: List[LocationValuationSummary]


# =====================
# Stock Movement Report
# =====================


class MovementType(str, Enum):
    RECEIVE = "receive"
    SHIP = "ship"
    TRANSFER = "transfer"
    ADJUST = "adjust"
    COUNT = "count"


class MovementReportItem(BaseModel):
    """Minimal item info for movement report."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    sku: str


class MovementReportLocation(BaseModel):
    """Minimal location info for movement report."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    code: str


class StockMovementReportEntry(BaseModel):
    """Individual movement entry in the report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    date: datetime
    inventory_item: MovementReportItem
    movement_type: MovementType
    quantity: int
    from_location: Optional[MovementReportLocation] = None
    to_location: Optional[MovementReportLocation] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    running_balance: int


class StockMovementReportSummary(BaseModel):
    """Summary statistics for movement report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_movements: int
    total_in: int
    total_out: int
    net_change: int


class StockMovementReport(BaseModel):
    """Complete stock movement report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # Summary
    summary: StockMovementReportSummary

    # Movement entries with running balance
    movements: List[StockMovementReportEntry]
