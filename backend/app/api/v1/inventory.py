import math
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.stock_movement import StockMovement as StockMovementModel
from app.models.inventory_location_quantity import (
    InventoryLocationQuantity as InventoryLocationQuantityModel,
)
from app.models.audit_log import AuditAction, EntityType
from app.models.item_revision import ItemRevision as ItemRevisionModel, RevisionType
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
from app.schemas.item_revision import (
    ItemRevision,
    ItemRevisionSummary,
    RevisionCompare,
    RestoreRevisionRequest,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
    MessageResponse,
)
from app.services.audit import audit_service
from app.services.storage import storage_service
from app.services.revision import revision_service

# All routes in this router require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


def add_image_url(item: InventoryItemModel) -> dict:
    """Convert inventory item to dict and add signed image URL if available."""
    item_dict = {
        "id": item.id,
        "name": item.name,
        "sku": item.sku,
        "description": item.description,
        "quantity": item.quantity,
        "reorder_point": item.reorder_point,
        "unit_price": item.unit_price,
        "status": item.status,
        "category_id": item.category_id,
        "location_id": item.location_id,
        "category": item.category,
        "location": item.location,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "created_by": item.created_by,
        "updated_by": item.updated_by,
        "image_key": item.image_key,
        "image_url": (
            storage_service.get_signed_url(item.image_key) if item.image_key else None
        ),
        "custom_attributes": item.custom_attributes,
    }
    return item_dict


@router.get("", response_model=ListResponse[InventoryItem])
def get_inventory_items(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=1000, alias="pageSize", description="Items per page"
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

    # Add signed image URLs to items
    items_with_urls = [add_image_url(item) for item in items]

    return ListResponse(
        data=items_with_urls,
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
    return DataResponse(data=add_image_url(item), meta=get_response_meta(request))


@router.post("", response_model=DataResponse[InventoryItem], status_code=201)
def create_inventory_item(
    item: InventoryItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new inventory item.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"[CREATE] Received item data: {item.model_dump()}")

    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    logger.info(f"[CREATE] Tenant: {tenant.id}")

    # Check if SKU already exists
    existing_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.sku == item.sku).first()
    )
    if existing_item:
        logger.warning(f"[CREATE] SKU already exists: {item.sku}")
        raise HTTPException(status_code=400, detail="SKU already exists")

    try:
        # Convert string UUIDs to proper UUID objects for foreign keys
        item_data = item.model_dump()
        if item_data.get("category_id"):
            item_data["category_id"] = UUID(item_data["category_id"])
        if item_data.get("location_id"):
            item_data["location_id"] = UUID(item_data["location_id"])

        # Create item with tenant_id from context
        db_item = InventoryItemModel(
            **item_data,
            tenant_id=tenant.id,
            created_by=user.id,
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"[CREATE] Item created successfully: {db_item.id}")
    except Exception as e:
        logger.error(f"[CREATE] Failed to create item: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create item: {str(e)}")

    # Log the creation
    if tenant:
        audit_service.log_create(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=db_item.id,
            entity_name=f"{db_item.sku} - {db_item.name}",
            data=item.model_dump(),
            request=request,
        )

        # Create initial revision
        revision_service.create_revision(
            db=db,
            tenant_id=tenant.id,
            item=db_item,
            user_id=user.id,
            revision_type=RevisionType.CREATE,
        )
        db.commit()

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
    return DataResponse(data=add_image_url(db_item), meta=get_response_meta(request))


@router.put("/{item_id}", response_model=DataResponse[InventoryItem])
def update_inventory_item(
    item_id: UUID,
    item: InventoryItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update an inventory item.
    """
    tenant = get_current_tenant()

    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Capture old values for audit and revision
    old_values = {
        "name": db_item.name,
        "sku": db_item.sku,
        "description": db_item.description,
        "quantity": db_item.quantity,
        "reorder_point": db_item.reorder_point,
        "unit_price": db_item.unit_price,
        "status": db_item.status,
        "category_id": str(db_item.category_id) if db_item.category_id else None,
        "location_id": str(db_item.location_id) if db_item.location_id else None,
        "image_key": db_item.image_key,
        "custom_attributes": db_item.custom_attributes,
    }

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db_item.updated_by = user.id
    db.commit()
    db.refresh(db_item)

    # Log the update with changes and create revision
    if tenant:
        # Build changes dict showing old/new values
        changes = {}
        for field, new_value in update_data.items():
            old_value = old_values.get(field)
            # Convert UUIDs to strings for JSON serialization
            if hasattr(new_value, "hex"):
                new_value = str(new_value)
            if hasattr(old_value, "hex"):
                old_value = str(old_value)
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}

        if changes:
            audit_service.log_update(
                db=db,
                tenant_id=tenant.id,
                user_id=user.id,
                entity_type=EntityType.INVENTORY_ITEM,
                entity_id=db_item.id,
                entity_name=f"{db_item.sku} - {db_item.name}",
                changes=changes,
                request=request,
            )

            # Create update revision
            revision_service.create_update_revision(
                db=db,
                tenant_id=tenant.id,
                item=db_item,
                old_values=old_values,
                user_id=user.id,
            )
            db.commit()

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
    return DataResponse(data=add_image_url(db_item), meta=get_response_meta(request))


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_inventory_item(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete an inventory item.
    """
    tenant = get_current_tenant()

    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Capture item info for audit before deleting
    item_name = f"{db_item.sku} - {db_item.name}"
    item_data = {
        "sku": db_item.sku,
        "name": db_item.name,
        "quantity": db_item.quantity,
        "status": db_item.status,
    }

    db.delete(db_item)
    db.commit()

    # Log the deletion
    if tenant:
        audit_service.log_delete(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=item_id,
            entity_name=item_name,
            data=item_data,
            request=request,
        )

    return MessageResponse(
        message="Item deleted successfully", meta=get_response_meta(request)
    )


@router.post("/bulk-delete", response_model=DataResponse[BulkOperationResult])
def bulk_delete_items(
    request_data: BulkDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete multiple inventory items at once.
    """
    tenant = get_current_tenant()
    success_count = 0
    failed_ids = []
    deleted_items = []

    for item_id in request_data.ids:
        try:
            db_item = (
                db.query(InventoryItemModel)
                .filter(InventoryItemModel.id == item_id)
                .first()
            )
            if db_item:
                deleted_items.append(
                    {
                        "id": str(db_item.id),
                        "sku": db_item.sku,
                        "name": db_item.name,
                    }
                )
                db.delete(db_item)
                success_count += 1
            else:
                failed_ids.append(item_id)
        except Exception:
            failed_ids.append(item_id)

    db.commit()

    # Log bulk delete operation
    if tenant and deleted_items:
        audit_service.log_bulk_operation(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            action=AuditAction.BULK_DELETE,
            entity_type=EntityType.INVENTORY_ITEM,
            count=success_count,
            data={"deleted_items": deleted_items},
            request=request,
        )

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
    user: User = Depends(get_current_user),
):
    """
    Update status for multiple inventory items at once.
    """
    tenant = get_current_tenant()
    success_count = 0
    failed_ids = []
    updated_items = []

    for item_id in request_data.ids:
        try:
            db_item = (
                db.query(InventoryItemModel)
                .filter(InventoryItemModel.id == item_id)
                .first()
            )
            if db_item:
                old_status = db_item.status
                db_item.status = request_data.status.value
                updated_items.append(
                    {
                        "id": str(db_item.id),
                        "sku": db_item.sku,
                        "old_status": old_status,
                        "new_status": request_data.status.value,
                    }
                )
                success_count += 1
            else:
                failed_ids.append(item_id)
        except Exception:
            failed_ids.append(item_id)

    db.commit()

    # Log bulk update operation
    if tenant and updated_items:
        audit_service.log_bulk_operation(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            action=AuditAction.BULK_UPDATE,
            entity_type=EntityType.INVENTORY_ITEM,
            count=success_count,
            data={
                "updated_items": updated_items,
                "new_status": request_data.status.value,
            },
            request=request,
        )

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
    user: User = Depends(get_current_user),
):
    """
    Quickly adjust the quantity of an inventory item.
    This updates the quantity directly and auto-updates the status based on the new quantity.
    """
    tenant = get_current_tenant()

    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Capture old values for audit
    old_quantity = db_item.quantity
    old_status = db_item.status

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

    # Log the quick adjustment as a stock adjustment
    if tenant:
        audit_service.log_stock_movement(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            movement_type=AuditAction.STOCK_ADJUST,
            item_id=db_item.id,
            item_name=f"{db_item.sku} - {db_item.name}",
            quantity_change=request_data.quantity - old_quantity,
            old_quantity=old_quantity,
            new_quantity=request_data.quantity,
            reason=request_data.reason,
            request=request,
        )

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


# =============================================================================
# Revision Control Endpoints
# =============================================================================


@router.get("/{item_id}/revisions", response_model=ListResponse[ItemRevisionSummary])
def get_item_revisions(
    item_id: UUID,
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    db: Session = Depends(get_db),
):
    """
    Get revision history for an inventory item.
    Returns a paginated list of revisions in reverse chronological order.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    revisions, total = revision_service.get_revisions(
        db=db,
        inventory_item_id=item_id,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ListResponse(
        data=revisions,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.get("/{item_id}/revisions/latest", response_model=DataResponse[ItemRevision])
def get_latest_revision(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get the latest revision for an inventory item.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    revision = revision_service.get_latest_revision(db=db, inventory_item_id=item_id)
    if not revision:
        raise HTTPException(status_code=404, detail="No revisions found for this item")

    return DataResponse(data=revision, meta=get_response_meta(request))


@router.get(
    "/{item_id}/revisions/{revision_number}", response_model=DataResponse[ItemRevision]
)
def get_item_revision(
    item_id: UUID,
    revision_number: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get a specific revision by revision number.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    revision = revision_service.get_revision(
        db=db,
        inventory_item_id=item_id,
        revision_number=revision_number,
    )
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    return DataResponse(data=revision, meta=get_response_meta(request))


@router.get(
    "/{item_id}/revisions/{from_rev}/compare/{to_rev}",
    response_model=DataResponse[RevisionCompare],
)
def compare_revisions(
    item_id: UUID,
    from_rev: int,
    to_rev: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Compare two revisions and return the differences.
    """
    # Verify item exists
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    comparison = revision_service.compare_revisions(
        db=db,
        inventory_item_id=item_id,
        from_revision_number=from_rev,
        to_revision_number=to_rev,
    )
    if not comparison:
        raise HTTPException(status_code=404, detail="One or both revisions not found")

    return DataResponse(data=comparison, meta=get_response_meta(request))


@router.post("/{item_id}/revisions/restore", response_model=DataResponse[InventoryItem])
def restore_revision(
    item_id: UUID,
    restore_request: RestoreRevisionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Restore an inventory item to a previous revision state.
    This creates a new revision of type RESTORE.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Get the item
    db_item = (
        db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Get the revision to restore
    revision = revision_service.get_revision(
        db=db,
        inventory_item_id=item_id,
        revision_number=restore_request.revision_number,
    )
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    # Restore the item to the revision state
    new_revision = revision_service.restore_revision(
        db=db,
        tenant_id=tenant.id,
        item=db_item,
        revision=revision,
        user_id=user.id,
        reason=restore_request.reason,
    )

    db.commit()

    # Log the restore action
    audit_service.log_update(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        entity_type=EntityType.INVENTORY_ITEM,
        entity_id=db_item.id,
        entity_name=f"{db_item.sku} - {db_item.name}",
        changes={"restored_to_revision": restore_request.revision_number},
        request=request,
    )

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

    return DataResponse(data=add_image_url(db_item), meta=get_response_meta(request))
