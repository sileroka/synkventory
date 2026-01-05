"""
Work Order API endpoints.

Provides REST API for managing work orders:
- CRUD operations
- Status management
- Progress tracking
- Building assemblies
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.work_order import WorkOrderStatus, WorkOrderPriority
from app.services.work_order import work_order_service
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderStatusUpdate,
    WorkOrderProgressUpdate,
    WorkOrderBuildRequest,
    WorkOrderResponse,
    WorkOrderListResponse,
    WorkOrderStats,
    WorkOrderItemSummary,
    WorkOrderLocationSummary,
    WorkOrderUserSummary,
)
from app.schemas.response import DataResponse, ListResponse, MessageResponse

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


def _serialize_work_order(wo) -> dict:
    """Convert a WorkOrder model to response dict."""
    data = {
        "id": wo.id,
        "work_order_number": wo.work_order_number,
        "item_id": wo.item_id,
        "quantity_ordered": wo.quantity_ordered,
        "quantity_completed": wo.quantity_completed,
        "quantity_scrapped": wo.quantity_scrapped,
        "quantity_remaining": wo.quantity_remaining,
        "completion_percentage": wo.completion_percentage,
        "status": wo.status,
        "priority": wo.priority,
        "due_date": wo.due_date,
        "start_date": wo.start_date,
        "completed_date": wo.completed_date,
        "is_overdue": wo.is_overdue,
        "output_location_id": wo.output_location_id,
        "assigned_to_id": wo.assigned_to_id,
        "description": wo.description,
        "notes": wo.notes,
        "estimated_cost": wo.estimated_cost,
        "actual_cost": wo.actual_cost,
        "created_at": wo.created_at,
        "updated_at": wo.updated_at,
        "created_by": wo.created_by,
        "updated_by": wo.updated_by,
    }
    
    # Add related objects
    if wo.item:
        data["item"] = {
            "id": wo.item.id,
            "sku": wo.item.sku,
            "name": wo.item.name,
            "total_quantity": wo.item.total_quantity,
        }
    
    if wo.output_location:
        data["output_location"] = {
            "id": wo.output_location.id,
            "name": wo.output_location.name,
            "code": wo.output_location.code,
        }
    
    if wo.assigned_to:
        data["assigned_to"] = {
            "id": wo.assigned_to.id,
            "email": wo.assigned_to.email,
            "first_name": wo.assigned_to.first_name,
            "last_name": wo.assigned_to.last_name,
        }
    
    return data


def _serialize_work_order_list(wo) -> dict:
    """Convert a WorkOrder model to list response dict."""
    data = {
        "id": wo.id,
        "work_order_number": wo.work_order_number,
        "item_id": wo.item_id,
        "quantity_ordered": wo.quantity_ordered,
        "quantity_completed": wo.quantity_completed,
        "quantity_remaining": wo.quantity_remaining,
        "completion_percentage": wo.completion_percentage,
        "status": wo.status,
        "priority": wo.priority,
        "due_date": wo.due_date,
        "is_overdue": wo.is_overdue,
        "created_at": wo.created_at,
    }
    
    if wo.item:
        data["item_sku"] = wo.item.sku
        data["item_name"] = wo.item.name
    
    if wo.assigned_to:
        name_parts = []
        if wo.assigned_to.first_name:
            name_parts.append(wo.assigned_to.first_name)
        if wo.assigned_to.last_name:
            name_parts.append(wo.assigned_to.last_name)
        data["assigned_to_name"] = " ".join(name_parts) if name_parts else wo.assigned_to.email
    
    return data


@router.get("", response_model=ListResponse[WorkOrderListResponse])
def list_work_orders(
    status: Optional[WorkOrderStatus] = Query(None, description="Filter by status"),
    priority: Optional[WorkOrderPriority] = Query(None, description="Filter by priority"),
    item_id: Optional[UUID] = Query(None, description="Filter by item"),
    assigned_to_id: Optional[UUID] = Query(None, description="Filter by assigned user"),
    include_completed: bool = Query(False, description="Include completed and cancelled orders"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of work orders."""
    work_orders, total = work_order_service.get_work_orders(
        db=db,
        status=status,
        priority=priority,
        item_id=item_id,
        assigned_to_id=assigned_to_id,
        include_completed=include_completed,
        page=page,
        page_size=page_size,
    )
    
    return ListResponse(
        data=[_serialize_work_order_list(wo) for wo in work_orders],
        meta={
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": (total + page_size - 1) // page_size,
        },
    )


@router.get("/stats", response_model=DataResponse[WorkOrderStats])
def get_work_order_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get work order statistics."""
    stats = work_order_service.get_stats(db)
    return DataResponse(data=stats)


@router.get("/{work_order_id}", response_model=DataResponse[WorkOrderResponse])
def get_work_order(
    work_order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single work order by ID."""
    work_order = work_order_service.get_work_order(db, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return DataResponse(data=_serialize_work_order(work_order))


@router.post("", response_model=DataResponse[WorkOrderResponse], status_code=201)
def create_work_order(
    data: WorkOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new work order."""
    try:
        work_order = work_order_service.create_work_order(
            db=db,
            data=data,
            user_id=current_user.id,
            request=request,
        )
        return DataResponse(data=_serialize_work_order(work_order))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{work_order_id}", response_model=DataResponse[WorkOrderResponse])
def update_work_order(
    work_order_id: UUID,
    data: WorkOrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a work order."""
    try:
        work_order = work_order_service.update_work_order(
            db=db,
            work_order_id=work_order_id,
            data=data,
            user_id=current_user.id,
            request=request,
        )
        return DataResponse(data=_serialize_work_order(work_order))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{work_order_id}/status", response_model=DataResponse[WorkOrderResponse])
def update_work_order_status(
    work_order_id: UUID,
    data: WorkOrderStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update work order status."""
    try:
        work_order = work_order_service.update_status(
            db=db,
            work_order_id=work_order_id,
            data=data,
            user_id=current_user.id,
            request=request,
        )
        return DataResponse(data=_serialize_work_order(work_order))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{work_order_id}/progress", response_model=DataResponse[WorkOrderResponse])
def record_progress(
    work_order_id: UUID,
    data: WorkOrderProgressUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record production progress."""
    try:
        work_order = work_order_service.record_progress(
            db=db,
            work_order_id=work_order_id,
            data=data,
            user_id=current_user.id,
            request=request,
        )
        return DataResponse(data=_serialize_work_order(work_order))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{work_order_id}/build", response_model=DataResponse[WorkOrderResponse])
def build_from_work_order(
    work_order_id: UUID,
    data: WorkOrderBuildRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Build assemblies for a work order.
    
    This will consume components from inventory and produce the assembly,
    then update the work order progress.
    """
    try:
        work_order = work_order_service.build_from_work_order(
            db=db,
            work_order_id=work_order_id,
            quantity=data.quantity,
            user_id=current_user.id,
            request=request,
        )
        return DataResponse(data=_serialize_work_order(work_order))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{work_order_id}", response_model=MessageResponse)
def delete_work_order(
    work_order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a work order (only draft or cancelled)."""
    try:
        work_order_service.delete_work_order(
            db=db,
            work_order_id=work_order_id,
            user_id=current_user.id,
            request=request,
        )
        return MessageResponse(message="Work order deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/item/{item_id}", response_model=ListResponse[WorkOrderListResponse])
def get_work_orders_for_item(
    item_id: UUID,
    include_completed: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all work orders for a specific item."""
    work_orders = work_order_service.get_work_orders_for_item(
        db=db,
        item_id=item_id,
        include_completed=include_completed,
    )
    
    return ListResponse(
        data=[_serialize_work_order_list(wo) for wo in work_orders],
        meta={
            "page": 1,
            "pageSize": len(work_orders),
            "totalItems": len(work_orders),
            "totalPages": 1,
        },
    )
