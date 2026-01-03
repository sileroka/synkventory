"""
Report endpoints for inventory analytics.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.stock_movement import StockMovement as StockMovementModel
from app.schemas.report import (
    InventoryValuationReport,
    ValuationItem,
    CategoryValuationSummary,
    LocationValuationSummary,
    StockMovementReport,
    StockMovementReportEntry,
    StockMovementReportSummary,
    MovementReportItem,
    MovementReportLocation,
)
from app.schemas.response import DataResponse, ResponseMeta

# All routes in this router require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/inventory-valuation", response_model=DataResponse[InventoryValuationReport]
)
def get_inventory_valuation(
    request: Request,
    category_ids: Optional[List[UUID]] = Query(
        None, alias="categoryIds", description="Filter by category IDs"
    ),
    location_ids: Optional[List[UUID]] = Query(
        None, alias="locationIds", description="Filter by location IDs"
    ),
    db: Session = Depends(get_db),
):
    """
    Get inventory valuation report with optional category and location filters.
    Returns item-level detail plus summaries grouped by category and location.
    """
    # Base query with relationships
    query = db.query(InventoryItemModel).options(
        joinedload(InventoryItemModel.category),
        joinedload(InventoryItemModel.location),
    )

    # Apply filters
    if category_ids:
        query = query.filter(InventoryItemModel.category_id.in_(category_ids))

    if location_ids:
        query = query.filter(InventoryItemModel.location_id.in_(location_ids))

    # Get all matching items
    items = query.all()

    # Build item-level valuation
    valuation_items: List[ValuationItem] = []
    for item in items:
        total_value = item.quantity * item.unit_price
        valuation_items.append(
            ValuationItem(
                id=str(item.id),
                sku=item.sku,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_value=total_value,
                category=(
                    {
                        "id": str(item.category.id),
                        "name": item.category.name,
                        "code": item.category.code,
                    }
                    if item.category
                    else None
                ),
                location=(
                    {
                        "id": str(item.location.id),
                        "name": item.location.name,
                        "code": item.location.code,
                    }
                    if item.location
                    else None
                ),
            )
        )

    # Calculate totals
    total_items = len(valuation_items)
    total_units = sum(item.quantity for item in valuation_items)
    total_value = sum(item.total_value for item in valuation_items)

    # Group by category
    category_groups: dict = {}
    for item in valuation_items:
        if item.category:
            key = item.category.id
            cat_name = item.category.name
            cat_code = item.category.code
        else:
            key = None
            cat_name = "Uncategorized"
            cat_code = None

        if key not in category_groups:
            category_groups[key] = {
                "category_id": key,
                "category_name": cat_name,
                "category_code": cat_code,
                "item_count": 0,
                "total_units": 0,
                "total_value": 0.0,
            }
        category_groups[key]["item_count"] += 1
        category_groups[key]["total_units"] += item.quantity
        category_groups[key]["total_value"] += item.total_value

    by_category = [
        CategoryValuationSummary(**data)
        for data in sorted(
            category_groups.values(), key=lambda x: x["total_value"], reverse=True
        )
    ]

    # Group by location
    location_groups: dict = {}
    for item in valuation_items:
        if item.location:
            key = item.location.id
            loc_name = item.location.name
            loc_code = item.location.code
        else:
            key = None
            loc_name = "Unassigned"
            loc_code = None

        if key not in location_groups:
            location_groups[key] = {
                "location_id": key,
                "location_name": loc_name,
                "location_code": loc_code,
                "item_count": 0,
                "total_units": 0,
                "total_value": 0.0,
            }
        location_groups[key]["item_count"] += 1
        location_groups[key]["total_units"] += item.quantity
        location_groups[key]["total_value"] += item.total_value

    by_location = [
        LocationValuationSummary(**data)
        for data in sorted(
            location_groups.values(), key=lambda x: x["total_value"], reverse=True
        )
    ]

    # Build report
    report = InventoryValuationReport(
        total_items=total_items,
        total_units=total_units,
        total_value=total_value,
        items=valuation_items,
        by_category=by_category,
        by_location=by_location,
    )

    return DataResponse(data=report, meta=get_response_meta(request))


@router.get("/stock-movements", response_model=DataResponse[StockMovementReport])
def get_stock_movement_report(
    request: Request,
    start_date: Optional[date] = Query(
        None, alias="startDate", description="Start date for the report (inclusive)"
    ),
    end_date: Optional[date] = Query(
        None, alias="endDate", description="End date for the report (inclusive)"
    ),
    item_ids: Optional[List[UUID]] = Query(
        None, alias="itemIds", description="Filter by inventory item IDs"
    ),
    location_ids: Optional[List[UUID]] = Query(
        None, alias="locationIds", description="Filter by location IDs (from or to)"
    ),
    movement_types: Optional[List[str]] = Query(
        None, alias="movementTypes", description="Filter by movement types"
    ),
    db: Session = Depends(get_db),
):
    """
    Get stock movement report with date range and filters.
    Returns movements with calculated running balance and summary statistics.
    """
    # Base query with relationships
    query = db.query(StockMovementModel).options(
        joinedload(StockMovementModel.inventory_item),
        joinedload(StockMovementModel.from_location),
        joinedload(StockMovementModel.to_location),
    )

    # Apply date range filters
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(StockMovementModel.created_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(StockMovementModel.created_at <= end_datetime)

    # Apply item filter
    if item_ids:
        query = query.filter(StockMovementModel.inventory_item_id.in_(item_ids))

    # Apply location filter (matches either from or to location)
    if location_ids:
        query = query.filter(
            (StockMovementModel.from_location_id.in_(location_ids))
            | (StockMovementModel.to_location_id.in_(location_ids))
        )

    # Apply movement type filter
    if movement_types:
        query = query.filter(StockMovementModel.movement_type.in_(movement_types))

    # Order by date ascending to calculate running balance
    query = query.order_by(StockMovementModel.created_at.asc())

    # Get all matching movements
    movements = query.all()

    # Calculate summary stats and build entries with running balance
    total_in = 0
    total_out = 0
    running_balance = 0
    entries: List[StockMovementReportEntry] = []

    for movement in movements:
        # Update running balance
        running_balance += movement.quantity

        # Track total in/out
        if movement.quantity > 0:
            total_in += movement.quantity
        else:
            total_out += abs(movement.quantity)

        # Build entry
        entry = StockMovementReportEntry(
            id=str(movement.id),
            date=movement.created_at,
            inventory_item=MovementReportItem(
                id=str(movement.inventory_item.id),
                name=movement.inventory_item.name,
                sku=movement.inventory_item.sku,
            ),
            movement_type=movement.movement_type.value,
            quantity=movement.quantity,
            from_location=(
                MovementReportLocation(
                    id=str(movement.from_location.id),
                    name=movement.from_location.name,
                    code=movement.from_location.code,
                )
                if movement.from_location
                else None
            ),
            to_location=(
                MovementReportLocation(
                    id=str(movement.to_location.id),
                    name=movement.to_location.name,
                    code=movement.to_location.code,
                )
                if movement.to_location
                else None
            ),
            reference_number=movement.reference_number,
            notes=movement.notes,
            running_balance=running_balance,
        )
        entries.append(entry)

    # Build summary
    summary = StockMovementReportSummary(
        total_movements=len(entries),
        total_in=total_in,
        total_out=total_out,
        net_change=total_in - total_out,
    )

    # Build report (entries in descending order for display)
    report = StockMovementReport(
        summary=summary,
        movements=list(reversed(entries)),  # Most recent first for display
    )

    return DataResponse(data=report, meta=get_response_meta(request))
