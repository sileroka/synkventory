import math
from uuid import UUID
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func as sql_func
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.stock_movement import StockMovement as StockMovementModel, MovementType
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.inventory_location_quantity import (
    InventoryLocationQuantity as InventoryLocationQuantityModel,
)
from app.models.audit_log import AuditAction, EntityType
from app.schemas.stock_movement import (
    StockMovement,
    StockMovementCreate,
    MovementType as MovementTypeSchema,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
)
from app.services.audit import audit_service
from app.services.lot import lot_service
from app.services.stock_movement_service import stock_movement_service

# All routes in this router require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


def update_inventory_status(item: InventoryItemModel) -> None:
    """Update inventory item status based on quantity vs reorder point."""
    if item.quantity <= 0:
        item.status = "out_of_stock"
    elif item.quantity <= item.reorder_point:
        item.status = "low_stock"
    else:
        item.status = "in_stock"


def recalculate_total_quantity(db: Session, inventory_item_id: str) -> int:
    """Recalculate total quantity from all location quantities."""
    result = (
        db.query(
            sql_func.coalesce(sql_func.sum(InventoryLocationQuantityModel.quantity), 0)
        )
        .filter(InventoryLocationQuantityModel.inventory_item_id == inventory_item_id)
        .scalar()
    )
    return int(result)


def get_or_create_location_quantity(
    db: Session, inventory_item_id: str, location_id: str
) -> InventoryLocationQuantityModel:
    """Get or create an inventory location quantity record."""
    loc_qty = (
        db.query(InventoryLocationQuantityModel)
        .filter(
            InventoryLocationQuantityModel.inventory_item_id == inventory_item_id,
            InventoryLocationQuantityModel.location_id == location_id,
        )
        .first()
    )
    if not loc_qty:
        loc_qty = InventoryLocationQuantityModel(
            inventory_item_id=inventory_item_id,
            location_id=location_id,
            quantity=0,
        )
        db.add(loc_qty)
        db.flush()
    return loc_qty


@router.post("", response_model=DataResponse[StockMovement], status_code=201)
def create_stock_movement(
    movement: StockMovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new stock movement and update inventory quantity using service.
    """
    db_movement = stock_movement_service.create_movement(
        db=db, movement=movement, user_id=user.id, request=request
    )
    return DataResponse(data=db_movement, meta=get_response_meta(request))


@router.get("", response_model=ListResponse[StockMovement])
def get_stock_movements(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    inventory_item_id: Optional[str] = Query(
        None, alias="inventoryItemId", description="Filter by inventory item"
    ),
    location_id: Optional[str] = Query(
        None, alias="locationId", description="Filter by location (from or to)"
    ),
    movement_type: Optional[MovementTypeSchema] = Query(
        None, alias="movementType", description="Filter by movement type"
    ),
    start_date: Optional[date] = Query(
        None, alias="startDate", description="Filter movements from this date"
    ),
    end_date: Optional[date] = Query(
        None, alias="endDate", description="Filter movements until this date"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve stock movements with optional filters.
    """
    # Build query with filters
    query = db.query(StockMovementModel)

    if inventory_item_id:
        query = query.filter(StockMovementModel.inventory_item_id == inventory_item_id)

    if location_id:
        query = query.filter(
            (StockMovementModel.from_location_id == location_id)
            | (StockMovementModel.to_location_id == location_id)
        )

    if movement_type:
        query = query.filter(
            StockMovementModel.movement_type == MovementType(movement_type.value)
        )

    if start_date:
        query = query.filter(
            StockMovementModel.created_at
            >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query = query.filter(
            StockMovementModel.created_at
            <= datetime.combine(end_date, datetime.max.time())
        )

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get movements with relationships loaded, ordered by created_at descending
    movements = (
        query.options(
            joinedload(StockMovementModel.inventory_item),
            joinedload(StockMovementModel.from_location),
            joinedload(StockMovementModel.to_location),
        )
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


@router.get("/{movement_id}", response_model=DataResponse[StockMovement])
def get_stock_movement(
    movement_id: UUID, request: Request, db: Session = Depends(get_db)
):
    """
    Get a specific stock movement by ID.
    """
    movement = (
        db.query(StockMovementModel)
        .options(
            joinedload(StockMovementModel.inventory_item),
            joinedload(StockMovementModel.from_location),
            joinedload(StockMovementModel.to_location),
        )
        .filter(StockMovementModel.id == movement_id)
        .first()
    )
    if not movement:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    return DataResponse(data=movement, meta=get_response_meta(request))
