import math
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.db.session import get_db
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.stock_movement import StockMovement as StockMovementModel
from app.models.inventory_location_quantity import (
    InventoryLocationQuantity as InventoryLocationQuantityModel,
)
from app.schemas.inventory import (
    InventoryItem,
    InventoryItemCreate,
    InventoryItemUpdate,
    LowStockAlert,
    BulkDeleteRequest,
    BulkStatusUpdateRequest,
    QuickAdjustRequest,
    BulkOperationResult,
)
from app.schemas.stock_movement import StockMovement
from app.schemas.inventory_location_quantity import InventoryLocationQuantity
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
    MessageResponse,
)

router = APIRouter()


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/", response_model=ListResponse[InventoryItem])
def get_inventory_items(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    category_ids: Optional[List[UUID]] = Query(
        None, alias="categoryIds", description="Filter by category IDs"
    ),
    location_ids: Optional[List[UUID]] = Query(
        None, alias="locationIds", description="Filter by location IDs"
    ),
    statuses: Optional[List[str]] = Query(None, description="Filter by status values"),
    sort_field: Optional[str] = Query(
        None, alias="sortField", description="Field to sort by"
    ),
    sort_order: Optional[int] = Query(
        None, alias="sortOrder", description="Sort order: 1 for asc, -1 for desc"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve inventory items with pagination, filtering, and sorting.
    """
    # Start query with relationships
    query = db.query(InventoryItemModel).options(
        joinedload(InventoryItemModel.category),
        joinedload(InventoryItemModel.location),
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                InventoryItemModel.name.ilike(search_term),
                InventoryItemModel.sku.ilike(search_term),
            )
        )

    # Apply category filter
    if category_ids:
        query = query.filter(InventoryItemModel.category_id.in_(category_ids))

    # Apply location filter
    if location_ids:
        query = query.filter(InventoryItemModel.location_id.in_(location_ids))

    # Apply status filter
    if statuses:
        query = query.filter(InventoryItemModel.status.in_(statuses))

    # Get total count before pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Apply sorting
    sort_mapping = {
        "name": InventoryItemModel.name,
        "sku": InventoryItemModel.sku,
        "quantity": InventoryItemModel.quantity,
        "reorderPoint": InventoryItemModel.reorder_point,
        "unitPrice": InventoryItemModel.unit_price,
        "status": InventoryItemModel.status,
        "createdAt": InventoryItemModel.created_at,
        "updatedAt": InventoryItemModel.updated_at,
    }

    if sort_field and sort_field in sort_mapping:
        column = sort_mapping[sort_field]
        if sort_order == -1:
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        # Default sort by name
        query = query.order_by(asc(InventoryItemModel.name))

    # Calculate offset and apply pagination
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()

    return ListResponse(
        data=items,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get("/alerts/low-stock", response_model=ListResponse[LowStockAlert])
def get_low_stock_alerts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    db: Session = Depends(get_db),
):
    """
    Get inventory items that are at or below their reorder point.
    Includes suggested order quantity (reorder_point * 2 - quantity).
    """
    # Query for low stock items (quantity <= reorder_point and not discontinued)
    query = (
        db.query(InventoryItemModel)
        .filter(InventoryItemModel.quantity <= InventoryItemModel.reorder_point)
        .filter(InventoryItemModel.status != "discontinued")
    )

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get items with relationships loaded
    items = (
        query.options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .order_by(
            (InventoryItemModel.reorder_point - InventoryItemModel.quantity).desc()
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Convert to LowStockAlert with suggested order quantity
    alerts = []
    for item in items:
        suggested_qty = max(0, (item.reorder_point * 2) - item.quantity)
        alerts.append(
            {
                "id": str(item.id),
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "reorder_point": item.reorder_point,
                "suggested_order_quantity": suggested_qty,
                "status": item.status,
                "category": item.category,
                "location": item.location,
            }
        )

    return ListResponse(
        data=alerts,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get("/{item_id}", response_model=DataResponse[InventoryItem])
def get_inventory_item(item_id: UUID, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific inventory item by ID.
    """
    item = (
        db.query(InventoryItemModel)
        .options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .filter(InventoryItemModel.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return DataResponse(data=item, meta=get_response_meta(request))


@router.post("/", response_model=DataResponse[InventoryItem], status_code=201)
def create_inventory_item(
    item: InventoryItemCreate, request: Request, db: Session = Depends(get_db)
):
    """
    Create a new inventory item.
    """
    # Check if SKU already exists
    existing_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.sku == item.sku).first()
    )
    if existing_item:
        raise HTTPException(status_code=400, detail="SKU already exists")

    db_item = InventoryItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # Reload with relationships
    db_item = (
        db.query(InventoryItemModel)
        .options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .filter(InventoryItemModel.id == db_item.id)
        .first()
    )
    return DataResponse(data=db_item, meta=get_response_meta(request))


@router.put("/{item_id}", response_model=DataResponse[InventoryItem])
def update_inventory_item(
    item_id: UUID,
    item: InventoryItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update an inventory item.
    """
    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    # Reload with relationships
    db_item = (
        db.query(InventoryItemModel)
        .options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .filter(InventoryItemModel.id == db_item.id)
        .first()
    )
    return DataResponse(data=db_item, meta=get_response_meta(request))


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_inventory_item(
    item_id: UUID, request: Request, db: Session = Depends(get_db)
):
    """
    Delete an inventory item.
    """
    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return MessageResponse(
        message="Item deleted successfully", meta=get_response_meta(request)
    )


@router.post("/bulk-delete", response_model=DataResponse[BulkOperationResult])
def bulk_delete_items(
    request_data: BulkDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Delete multiple inventory items at once.
    """
    success_count = 0
    failed_ids = []

    for item_id in request_data.ids:
        try:
            db_item = (
                db.query(InventoryItemModel)
                .filter(InventoryItemModel.id == item_id)
                .first()
            )
            if db_item:
                db.delete(db_item)
                success_count += 1
            else:
                failed_ids.append(item_id)
        except Exception:
            failed_ids.append(item_id)

    db.commit()

    return DataResponse(
        data=BulkOperationResult(
            success_count=success_count,
            failed_count=len(failed_ids),
            failed_ids=failed_ids,
        ),
        meta=get_response_meta(request),
    )


@router.post("/bulk-status-update", response_model=DataResponse[BulkOperationResult])
def bulk_update_status(
    request_data: BulkStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update status for multiple inventory items at once.
    """
    success_count = 0
    failed_ids = []

    for item_id in request_data.ids:
        try:
            db_item = (
                db.query(InventoryItemModel)
                .filter(InventoryItemModel.id == item_id)
                .first()
            )
            if db_item:
                db_item.status = request_data.status.value
                success_count += 1
            else:
                failed_ids.append(item_id)
        except Exception:
            failed_ids.append(item_id)

    db.commit()

    return DataResponse(
        data=BulkOperationResult(
            success_count=success_count,
            failed_count=len(failed_ids),
            failed_ids=failed_ids,
        ),
        meta=get_response_meta(request),
    )


@router.post("/{item_id}/quick-adjust", response_model=DataResponse[InventoryItem])
def quick_adjust_quantity(
    item_id: UUID,
    request_data: QuickAdjustRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Quickly adjust the quantity of an inventory item.
    This updates the quantity directly and auto-updates the status based on the new quantity.
    """
    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update quantity
    db_item.quantity = request_data.quantity

    # Auto-update status based on quantity
    if db_item.quantity == 0:
        db_item.status = "out_of_stock"
    elif db_item.quantity <= db_item.reorder_point:
        db_item.status = "low_stock"
    else:
        db_item.status = "in_stock"

    db.commit()
    db.refresh(db_item)

    # Reload with relationships
    db_item = (
        db.query(InventoryItemModel)
        .options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .filter(InventoryItemModel.id == db_item.id)
        .first()
    )
    return DataResponse(data=db_item, meta=get_response_meta(request))


@router.get("/{item_id}/movements", response_model=ListResponse[StockMovement])
def get_inventory_item_movements(
    item_id: UUID,
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    db: Session = Depends(get_db),
):
    """
    Get stock movements for a specific inventory item.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Get total count
    total_items = (
        db.query(StockMovementModel)
        .filter(StockMovementModel.inventory_item_id == item_id)
        .count()
    )
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get movements with relationships loaded
    movements = (
        db.query(StockMovementModel)
        .options(
            joinedload(StockMovementModel.inventory_item),
            joinedload(StockMovementModel.from_location),
            joinedload(StockMovementModel.to_location),
        )
        .filter(StockMovementModel.inventory_item_id == item_id)
        .order_by(StockMovementModel.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return ListResponse(
        data=movements,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{item_id}/locations", response_model=ListResponse[InventoryLocationQuantity]
)
def get_inventory_item_locations(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get quantity breakdown by location for a specific inventory item.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Get all location quantities for this item
    location_quantities = (
        db.query(InventoryLocationQuantityModel)
        .options(joinedload(InventoryLocationQuantityModel.location))
        .filter(InventoryLocationQuantityModel.inventory_item_id == item_id)
        .filter(
            InventoryLocationQuantityModel.quantity > 0
        )  # Only show locations with stock
        .all()
    )

    return ListResponse(
        data=location_quantities,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=1,
            page_size=len(location_quantities),
            total_items=len(location_quantities),
            total_pages=1,
        ),
    )
