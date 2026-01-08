"""
Item Lots API endpoints for serial/lot/batch tracking.

Provides endpoints for:
- Listing lots for an inventory item with optional filters
- Creating new lots with serial numbers and expiration dates
- Updating lot details
- Deleting lots and adjusting inventory
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.item_lot import ItemLot as ItemLotModel
from app.schemas.item_lot import (
    ItemLotResponse,
    ItemLotCreate,
    ItemLotUpdate,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
    MessageResponse,
)
from app.services.lot import lot_service

import math

# All routes require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


def serialize_lot(lot: ItemLotModel) -> dict:
    """Convert ItemLot model to response dict with relationships."""
    lot_dict = {
        "id": str(lot.id),
        "item_id": str(lot.item_id),
        "lot_number": lot.lot_number,
        "serial_number": lot.serial_number,
        "quantity": lot.quantity,
        "expiration_date": lot.expiration_date,
        "manufacture_date": lot.manufacture_date,
        "location_id": str(lot.location_id) if lot.location_id else None,
        "created_at": lot.created_at,
        "updated_at": lot.updated_at,
        "created_by": str(lot.created_by) if lot.created_by else None,
        "updated_by": str(lot.updated_by) if lot.updated_by else None,
    }

    # Add nested relationships if loaded
    if lot.item:
        lot_dict["item"] = {
            "id": str(lot.item.id),
            "name": lot.item.name,
            "sku": lot.item.sku,
        }

    if lot.location:
        lot_dict["location"] = {
            "id": str(lot.location.id),
            "name": lot.location.name,
            "code": lot.location.code,
        }

    return lot_dict


# ============================================================================
# Item Lots CRUD Endpoints
# ============================================================================


@router.get(
    "/items/{item_id}/lots",
    response_model=ListResponse[ItemLotResponse],
)
def get_item_lots(
    request: Request,
    item_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=1000, alias="pageSize", description="Items per page"
    ),
    location_id: Optional[UUID] = Query(
        None, alias="locationId", description="Filter by location"
    ),
    include_expired: bool = Query(
        False, alias="includeExpired", description="Include expired lots"
    ),
    order_by: str = Query(
        "created_at",
        alias="orderBy",
        description="Sort by: created_at, expiration_date, lot_number",
    ),
    db: Session = Depends(get_db),
):
    """
    Get all lots for an inventory item with pagination and filters.

    Query parameters:
    - location_id: Filter by storage location
    - include_expired: Include or exclude expired lots
    - order_by: Sort field (created_at, expiration_date, lot_number)
    """
    try:
        # Get all lots matching filters
        all_lots = lot_service.get_lots(
            db=db,
            item_id=item_id,
            location_id=location_id,
            include_expired=include_expired,
            order_by=order_by,
        )

        # Calculate pagination
        total_items = len(all_lots)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Slice data for current page
        page_lots = all_lots[start_idx:end_idx]

        return ListResponse(
            data=[serialize_lot(lot) for lot in page_lots],
            meta=PaginationMeta(
                timestamp=datetime.utcnow(),
                request_id=getattr(request.state, "request_id", None),
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/items/{item_id}/lots",
    response_model=DataResponse[ItemLotResponse],
    status_code=201,
)
def create_item_lot(
    request: Request,
    item_id: UUID,
    lot_data: ItemLotCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new lot for an inventory item.

    The item_id from the URL path is used as the parent item.
    """
    tenant = get_current_tenant()

    try:
        lot = lot_service.create_lot(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            item_id=item_id,
            lot_number=lot_data.lot_number,
            quantity=lot_data.quantity,
            serial_number=lot_data.serial_number,
            expiration_date=lot_data.expiration_date,
            manufacture_date=lot_data.manufacture_date,
            location_id=lot_data.location_id,
            request=request,
        )

        # Refresh to get relationships
        lot = lot_service.get_lot_by_id(db, lot.id)

        return DataResponse(
            data=serialize_lot(lot),
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/lots/{lot_id}",
    response_model=DataResponse[ItemLotResponse],
)
def update_item_lot(
    request: Request,
    lot_id: UUID,
    lot_data: ItemLotUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing lot.

    All fields are optional. Only provided fields will be updated.
    """
    tenant = get_current_tenant()

    try:
        lot = lot_service.update_lot(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            lot_id=lot_id,
            lot_number=lot_data.lot_number,
            serial_number=lot_data.serial_number,
            quantity=lot_data.quantity,
            expiration_date=lot_data.expiration_date,
            manufacture_date=lot_data.manufacture_date,
            location_id=lot_data.location_id,
            request=request,
        )

        # Refresh to get relationships
        lot = lot_service.get_lot_by_id(db, lot.id)

        return DataResponse(
            data=serialize_lot(lot),
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/lots/{lot_id}",
    response_model=MessageResponse,
)
def delete_item_lot(
    request: Request,
    lot_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a lot and remove it from inventory tracking.

    The parent item's total_quantity will be automatically recalculated.
    """
    tenant = get_current_tenant()

    try:
        lot_service.delete_lot(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            lot_id=lot_id,
            request=request,
        )

        return MessageResponse(
            message="Lot deleted successfully",
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
