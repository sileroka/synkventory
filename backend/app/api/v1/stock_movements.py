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
    Create a new stock movement and update inventory quantity.

    Movement types and their effects:
    - receive: Positive quantity, adds to to_location
    - ship: Negative quantity, removes from from_location
    - transfer: Moves stock between locations
    - adjust: Manual adjustment at to_location (positive) or from_location (negative)
    - count: Physical count adjustment at to_location

    Location quantities are updated based on movement type:
    - receive/adjust(+)/count: to_location_id required, adds quantity there
    - ship/adjust(-): from_location_id required, removes quantity from there
    - transfer: both required, removes from from_location, adds to to_location
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Get the inventory item
    item = (
        db.query(InventoryItemModel)
        .filter(InventoryItemModel.id == movement.inventory_item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Capture old quantity for audit
    old_quantity = item.quantity

    # Validate transfer has both from and to locations
    if movement.movement_type == MovementTypeSchema.TRANSFER:
        if not movement.from_location_id or not movement.to_location_id:
            raise HTTPException(
                status_code=400,
                detail="Transfer movements require both from_location_id and to_location_id",
            )
        # For transfers, quantity should be positive (amount being moved)
        if movement.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Transfer quantity must be positive",
            )

    # Validate location requirements based on movement type
    if movement.movement_type in [MovementTypeSchema.RECEIVE, MovementTypeSchema.COUNT]:
        if not movement.to_location_id:
            raise HTTPException(
                status_code=400,
                detail=f"{movement.movement_type.value} movements require to_location_id",
            )
    elif movement.movement_type == MovementTypeSchema.SHIP:
        if not movement.from_location_id:
            raise HTTPException(
                status_code=400,
                detail="Ship movements require from_location_id",
            )
    elif movement.movement_type == MovementTypeSchema.ADJUST:
        # Adjustments: positive needs to_location, negative needs from_location
        if movement.quantity > 0 and not movement.to_location_id:
            raise HTTPException(
                status_code=400,
                detail="Positive adjustments require to_location_id",
            )
        if movement.quantity < 0 and not movement.from_location_id:
            raise HTTPException(
                status_code=400,
                detail="Negative adjustments require from_location_id",
            )

    # Update location-specific quantities
    if movement.movement_type == MovementTypeSchema.TRANSFER:
        # Transfer: remove from source, add to destination
        from_loc_qty = get_or_create_location_quantity(
            db, movement.inventory_item_id, movement.from_location_id
        )
        if from_loc_qty.quantity < movement.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity at source location. Available: {from_loc_qty.quantity}",
            )
        from_loc_qty.quantity -= movement.quantity
        from_loc_qty.updated_at = datetime.utcnow()

        to_loc_qty = get_or_create_location_quantity(
            db, movement.inventory_item_id, movement.to_location_id
        )
        to_loc_qty.quantity += movement.quantity
        to_loc_qty.updated_at = datetime.utcnow()

    elif movement.from_location_id and movement.quantity < 0:
        # Removing from a location (ship, negative adjust)
        from_loc_qty = get_or_create_location_quantity(
            db, movement.inventory_item_id, movement.from_location_id
        )
        new_loc_qty = from_loc_qty.quantity + movement.quantity  # quantity is negative
        if new_loc_qty < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity at location. Available: {from_loc_qty.quantity}",
            )
        from_loc_qty.quantity = new_loc_qty
        from_loc_qty.updated_at = datetime.utcnow()

    elif movement.to_location_id and movement.quantity > 0:
        # Adding to a location (receive, count, positive adjust)
        to_loc_qty = get_or_create_location_quantity(
            db, movement.inventory_item_id, movement.to_location_id
        )
        to_loc_qty.quantity += movement.quantity
        to_loc_qty.updated_at = datetime.utcnow()

    # Create the movement record with tenant_id
    lot_id = None

    # Handle lot operations based on movement type
    if movement.lot_id:
        lot_id = (
            UUID(movement.lot_id)
            if isinstance(movement.lot_id, str)
            else movement.lot_id
        )

    # For RECEIVE: create/update lot if needed
    if movement.movement_type == MovementTypeSchema.RECEIVE and movement.lot_id:
        lot = lot_service.get_lot_by_id(db, lot_id)
        if lot:
            # Update existing lot quantity
            lot.quantity += movement.quantity
            lot.updated_by = user.id
            db.flush()
        else:
            raise HTTPException(
                status_code=404,
                detail="Specified lot not found",
            )
    # For SHIP/TRANSFER: decrement lot quantity
    elif movement.lot_id and movement.movement_type in [
        MovementTypeSchema.SHIP,
        MovementTypeSchema.TRANSFER,
    ]:
        lot = lot_service.get_lot_by_id(db, lot_id)
        if not lot:
            raise HTTPException(
                status_code=404,
                detail="Specified lot not found",
            )
        decrement_qty = abs(movement.quantity)
        if lot.quantity < decrement_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity in lot. Available: {lot.quantity}",
            )
        lot.quantity -= decrement_qty
        lot.updated_by = user.id

        # Update lot location for transfers
        if (
            movement.movement_type == MovementTypeSchema.TRANSFER
            and movement.to_location_id
        ):
            lot.location_id = (
                UUID(movement.to_location_id)
                if isinstance(movement.to_location_id, str)
                else movement.to_location_id
            )

        db.flush()

    db_movement = StockMovementModel(
        inventory_item_id=movement.inventory_item_id,
        movement_type=MovementType(movement.movement_type.value),
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        lot_id=lot_id,
        reference_number=movement.reference_number,
        notes=movement.notes,
        tenant_id=tenant.id,
        created_by=user.id,
    )
    db.add(db_movement)

    # Recalculate total inventory quantity from all locations
    item.quantity = recalculate_total_quantity(db, movement.inventory_item_id)
    item.updated_at = datetime.utcnow()

    # Auto-update status based on quantity
    update_inventory_status(item)

    db.commit()
    db.refresh(db_movement)

    # Map movement type to audit action
    movement_type_to_audit_action = {
        MovementTypeSchema.RECEIVE: AuditAction.STOCK_RECEIVE,
        MovementTypeSchema.SHIP: AuditAction.STOCK_SHIP,
        MovementTypeSchema.TRANSFER: AuditAction.STOCK_TRANSFER,
        MovementTypeSchema.ADJUST: AuditAction.STOCK_ADJUST,
        MovementTypeSchema.COUNT: AuditAction.STOCK_COUNT,
    }
    audit_action = movement_type_to_audit_action.get(
        movement.movement_type, AuditAction.STOCK_ADJUST
    )

    # Log the stock movement
    if tenant:
        audit_service.log_stock_movement(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            movement_type=audit_action,
            item_id=item.id,
            item_name=f"{item.sku} - {item.name}",
            quantity_change=movement.quantity,
            old_quantity=old_quantity,
            new_quantity=item.quantity,
            from_location_id=movement.from_location_id,
            to_location_id=movement.to_location_id,
            reference_number=movement.reference_number,
            reason=movement.notes,
            request=request,
        )

    # Reload with relationships
    db_movement = (
        db.query(StockMovementModel)
        .options(
            joinedload(StockMovementModel.inventory_item),
            joinedload(StockMovementModel.from_location),
            joinedload(StockMovementModel.to_location),
        )
        .filter(StockMovementModel.id == db_movement.id)
        .first()
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
