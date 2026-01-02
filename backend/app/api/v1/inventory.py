import math
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.inventory import InventoryItem as InventoryItemModel
from app.schemas.inventory import (
    InventoryItem,
    InventoryItemCreate,
    InventoryItemUpdate,
)
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
    db: Session = Depends(get_db),
):
    """
    Retrieve inventory items with pagination.
    """
    # Get total count
    total_items = db.query(InventoryItemModel).count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get items with relationships loaded
    items = (
        db.query(InventoryItemModel)
        .options(
            joinedload(InventoryItemModel.category),
            joinedload(InventoryItemModel.location),
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )

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
