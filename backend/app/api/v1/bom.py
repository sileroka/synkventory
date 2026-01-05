"""
Bill of Materials API endpoints.

Provides endpoints for:
- Managing BOM component entries (CRUD)
- Calculating build availability
- Building assemblies from components
- Disassembling items back into components
- Where-used queries (find assemblies using a component)
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
from app.models.bill_of_material import BillOfMaterial as BillOfMaterialModel
from app.schemas.bill_of_material import (
    BillOfMaterial,
    BillOfMaterialCreate,
    BillOfMaterialUpdate,
    BillOfMaterialSummary,
    BOMAvailability,
    BOMBuildRequest,
    BOMBuildResult,
    BOMUnbuildRequest,
    BOMUnbuildResult,
    BOMComponentItem,
    WhereUsedEntry,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    ResponseMeta,
    MessageResponse,
)
from app.services.bom import bom_service
from app.services.storage import storage_service

# All routes require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


def serialize_bom_entry(entry: BillOfMaterialModel) -> dict:
    """Convert BOM entry to response dict with component details."""
    component = entry.component_item
    component_data = None
    
    if component:
        component_data = {
            "id": str(component.id),
            "name": component.name,
            "sku": component.sku,
            "quantity": component.quantity,
            "unit_price": component.unit_price,
            "status": component.status,
            "image_url": storage_service.get_signed_url(component.image_key) if component.image_key else None,
        }
    
    return {
        "id": str(entry.id),
        "parent_item_id": str(entry.parent_item_id),
        "component_item_id": str(entry.component_item_id),
        "quantity_required": entry.quantity_required,
        "unit_of_measure": entry.unit_of_measure,
        "notes": entry.notes,
        "display_order": entry.display_order,
        "component_item": component_data,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "created_by": str(entry.created_by) if entry.created_by else None,
        "updated_by": str(entry.updated_by) if entry.updated_by else None,
    }


def serialize_where_used_entry(entry: BillOfMaterialModel) -> dict:
    """Convert BOM entry to where-used response with parent details."""
    parent = entry.parent_item
    parent_data = None
    
    if parent:
        parent_data = {
            "id": str(parent.id),
            "name": parent.name,
            "sku": parent.sku,
            "quantity": parent.quantity,
            "unit_price": parent.unit_price,
            "status": parent.status,
            "image_url": storage_service.get_signed_url(parent.image_key) if parent.image_key else None,
        }
    
    return {
        "id": str(entry.id),
        "parent_item_id": str(entry.parent_item_id),
        "parent_item": parent_data,
        "quantity_required": entry.quantity_required,
        "unit_of_measure": entry.unit_of_measure,
    }


# ============================================================================
# BOM Component CRUD Endpoints
# ============================================================================


@router.get("/items/{item_id}/bom", response_model=ListResponse[BillOfMaterial])
def get_item_bom(
    request: Request,
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all BOM components for an item.
    
    Returns the list of components needed to build this item.
    """
    bom_entries = bom_service.get_bom_components(db, item_id)
    
    return ListResponse(
        data=[serialize_bom_entry(entry) for entry in bom_entries],
        meta=get_response_meta(request),
    )


@router.post("/items/{item_id}/bom", response_model=DataResponse[BillOfMaterial])
def add_bom_component(
    request: Request,
    item_id: UUID,
    bom_data: BillOfMaterialCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a component to an item's BOM.
    
    The parent_item_id in the request body will be ignored; the item_id
    from the URL path is used instead.
    """
    tenant = get_current_tenant()
    
    try:
        bom_entry = bom_service.create_bom_entry(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            parent_item_id=item_id,  # Use URL path item_id
            component_item_id=UUID(bom_data.component_item_id),
            quantity_required=bom_data.quantity_required,
            unit_of_measure=bom_data.unit_of_measure,
            notes=bom_data.notes,
            display_order=bom_data.display_order,
            request=request,
        )
        
        # Reload with relationships
        bom_entries = bom_service.get_bom_components(db, item_id)
        created_entry = next(
            (e for e in bom_entries if e.id == bom_entry.id),
            bom_entry
        )
        
        return DataResponse(
            data=serialize_bom_entry(created_entry),
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/bom/{bom_id}", response_model=DataResponse[BillOfMaterial])
def update_bom_component(
    request: Request,
    bom_id: UUID,
    bom_data: BillOfMaterialUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a BOM component entry."""
    tenant = get_current_tenant()
    
    try:
        bom_entry = bom_service.update_bom_entry(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            bom_id=bom_id,
            quantity_required=bom_data.quantity_required,
            unit_of_measure=bom_data.unit_of_measure,
            notes=bom_data.notes,
            display_order=bom_data.display_order,
            request=request,
        )
        
        # Reload with relationships
        bom_entries = bom_service.get_bom_components(db, bom_entry.parent_item_id)
        updated_entry = next(
            (e for e in bom_entries if e.id == bom_entry.id),
            bom_entry
        )
        
        return DataResponse(
            data=serialize_bom_entry(updated_entry),
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/bom/{bom_id}", response_model=MessageResponse)
def delete_bom_component(
    request: Request,
    bom_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a component from an item's BOM."""
    tenant = get_current_tenant()
    
    try:
        bom_service.delete_bom_entry(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            bom_id=bom_id,
            request=request,
        )
        
        return MessageResponse(
            message="BOM component removed successfully",
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Where-Used Query
# ============================================================================


@router.get("/items/{item_id}/where-used", response_model=ListResponse[WhereUsedEntry])
def get_where_used(
    request: Request,
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all assemblies where this item is used as a component.
    
    Useful for understanding the impact of changes to a component item.
    """
    where_used = bom_service.get_where_used(db, item_id)
    
    return ListResponse(
        data=[serialize_where_used_entry(entry) for entry in where_used],
        meta=get_response_meta(request),
    )


# ============================================================================
# Build/Unbuild Operations
# ============================================================================


@router.get("/items/{item_id}/bom/availability", response_model=DataResponse[BOMAvailability])
def get_build_availability(
    request: Request,
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Calculate how many assemblies can be built with current stock.
    
    Returns detailed availability for each component and identifies
    the limiting component(s).
    """
    try:
        availability = bom_service.calculate_availability(db, item_id)
        
        return DataResponse(
            data=availability,
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/items/{item_id}/bom/build", response_model=DataResponse[BOMBuildResult])
def build_assembly(
    request: Request,
    item_id: UUID,
    build_request: BOMBuildRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build assemblies from components.
    
    This will:
    - Decrease component item quantities based on BOM
    - Increase the parent item quantity
    - Create stock movements for audit trail
    """
    tenant = get_current_tenant()
    
    try:
        result = bom_service.build_assembly(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            parent_item_id=item_id,
            quantity_to_build=build_request.quantity_to_build,
            notes=build_request.notes,
            request=request,
        )
        
        return DataResponse(
            data=result,
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/items/{item_id}/bom/unbuild", response_model=DataResponse[BOMUnbuildResult])
def unbuild_assembly(
    request: Request,
    item_id: UUID,
    unbuild_request: BOMUnbuildRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disassemble items back into components.
    
    This will:
    - Decrease the parent item quantity
    - Increase component item quantities based on BOM
    - Create stock movements for audit trail
    """
    tenant = get_current_tenant()
    
    try:
        result = bom_service.unbuild_assembly(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            parent_item_id=item_id,
            quantity_to_unbuild=unbuild_request.quantity_to_unbuild,
            notes=unbuild_request.notes,
            request=request,
        )
        
        return DataResponse(
            data=result,
            meta=get_response_meta(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
