"""
API endpoints for Purchase Orders.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.purchase_order import PurchaseOrderStatus, PurchaseOrderPriority
from app.models.user import User
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListItem,
    PurchaseOrderDetail,
    PurchaseOrderStatusUpdate,
    PurchaseOrderLineItemCreate,
    PurchaseOrderLineItemResponse,
    PurchaseOrderLineItemWithItem,
    PurchaseOrderStats,
    LowStockSuggestion,
    ReceiveItemsRequest,
)
from app.schemas.response import PaginatedResponse, APIResponse
from app.services.purchase_order import purchase_order_service

router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _po_to_list_item(po) -> PurchaseOrderListItem:
    """Convert a PurchaseOrder to a list item schema."""
    item_count = len(po.line_items) if hasattr(po, 'line_items') and po.line_items else 0
    items_received = sum(
        1 for li in (po.line_items or [])
        if li.quantity_received >= li.quantity_ordered
    ) if hasattr(po, 'line_items') and po.line_items else 0
    supplier_details = po.supplier if hasattr(po, 'supplier') else None
    supplier_name = po.supplier_display_name if hasattr(po, 'supplier_display_name') else po.supplier_name
    
    return PurchaseOrderListItem(
        id=po.id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=supplier_name,
        status=po.status.value if hasattr(po.status, 'value') else po.status,
        priority=po.priority.value if hasattr(po.priority, 'value') else po.priority,
        total_amount=po.total_amount,
        order_date=po.order_date,
        expected_date=po.expected_date,
        received_date=po.received_date,
        auto_generated=po.auto_generated,
        created_at=po.created_at,
        item_count=item_count,
        items_received=items_received,
        requested_by_name=po.requested_by.name if po.requested_by else None,
        is_overdue=po.is_overdue,
        supplier=supplier_details,
    )


def _po_to_detail(po) -> PurchaseOrderDetail:
    """Convert a PurchaseOrder to a detail schema."""
    line_items = []
    for li in (po.line_items or []):
        line_items.append(PurchaseOrderLineItemWithItem(
            id=li.id,
            purchase_order_id=li.purchase_order_id,
            item_id=li.item_id,
            quantity_ordered=li.quantity_ordered,
            quantity_received=li.quantity_received,
            unit_price=li.unit_price,
            line_total=li.line_total,
            notes=li.notes,
            created_at=li.created_at,
            updated_at=li.updated_at,
            quantity_remaining=li.quantity_remaining,
            item_name=li.item.name if li.item else None,
            item_sku=li.item.sku if li.item else None,
            current_quantity=li.item.quantity if li.item else None,
            reorder_point=li.item.reorder_point if li.item else None,
        ))
    
    supplier_details = po.supplier if hasattr(po, 'supplier') else None
    supplier_name = po.supplier_display_name if hasattr(po, 'supplier_display_name') else po.supplier_name

    return PurchaseOrderDetail(
        id=po.id,
        tenant_id=po.tenant_id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=supplier_name,
        supplier_contact=po.supplier_contact,
        supplier_email=po.supplier_email,
        supplier_phone=po.supplier_phone,
        status=po.status.value if hasattr(po.status, 'value') else po.status,
        priority=po.priority.value if hasattr(po.priority, 'value') else po.priority,
        order_date=po.order_date,
        expected_date=po.expected_date,
        received_date=po.received_date,
        receiving_location_id=po.receiving_location_id,
        requested_by_id=po.requested_by_id,
        approved_by_id=po.approved_by_id,
        notes=po.notes,
        external_reference=po.external_reference,
        subtotal=po.subtotal,
        tax_amount=po.tax_amount,
        shipping_cost=po.shipping_cost,
        total_amount=po.total_amount,
        auto_generated=po.auto_generated,
        created_at=po.created_at,
        updated_at=po.updated_at,
        created_by=po.created_by,
        line_items=line_items,
        requested_by_name=po.requested_by.name if po.requested_by else None,
        approved_by_name=po.approved_by.name if po.approved_by else None,
        receiving_location_name=po.receiving_location.name if po.receiving_location else None,
        is_overdue=po.is_overdue,
        supplier=supplier_details,
    )


# =============================================================================
# LIST / CREATE
# =============================================================================

@router.get("", response_model=PaginatedResponse[PurchaseOrderListItem])
def list_purchase_orders(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    include_received: bool = False,
    supplier_name: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of purchase orders."""
    status_enum = None
    if status:
        try:
            status_enum = PurchaseOrderStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )
    
    priority_enum = None
    if priority:
        try:
            priority_enum = PurchaseOrderPriority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}",
            )
    
    purchase_orders, total = purchase_order_service.get_purchase_orders(
        db=db,
        page=page,
        page_size=page_size,
        status=status_enum,
        priority=priority_enum,
        include_received=include_received,
        supplier_name=supplier_name,
    )
    
    items = [_po_to_list_item(po) for po in purchase_orders]
    
    return PaginatedResponse(
        data=items,
        meta={
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": (total + page_size - 1) // page_size,
        },
    )


@router.post("", response_model=APIResponse[PurchaseOrderDetail], status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    request: Request,
    data: PurchaseOrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new purchase order."""
    try:
        po = purchase_order_service.create_purchase_order(
            db=db,
            data=data,
            user_id=user.id,
            request=request,
        )
        
        # Re-fetch with all relationships
        po = purchase_order_service.get_purchase_order(db, po.id)
        
        return APIResponse(data=_po_to_detail(po))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# STATS
# =============================================================================

@router.get("/stats", response_model=APIResponse[PurchaseOrderStats])
def get_purchase_order_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get purchase order statistics."""
    stats = purchase_order_service.get_stats(db)
    return APIResponse(data=stats)


# =============================================================================
# LOW STOCK
# =============================================================================

@router.get("/low-stock", response_model=APIResponse[LowStockSuggestion])
def get_low_stock_suggestions(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get low stock items that need reordering."""
    suggestion = purchase_order_service.get_low_stock_items(db, limit=limit)
    return APIResponse(data=suggestion)


@router.post("/from-low-stock", response_model=APIResponse[PurchaseOrderDetail], status_code=status.HTTP_201_CREATED)
def create_po_from_low_stock(
    request: Request,
    item_ids: List[UUID],
    supplier_name: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a purchase order from selected low stock items."""
    try:
        po = purchase_order_service.create_po_from_low_stock(
            db=db,
            item_ids=item_ids,
            user_id=user.id,
            supplier_name=supplier_name,
            request=request,
        )
        
        # Re-fetch with relationships
        po = purchase_order_service.get_purchase_order(db, po.id)
        
        return APIResponse(data=_po_to_detail(po))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# SINGLE PO OPERATIONS
# =============================================================================

@router.get("/{po_id}", response_model=APIResponse[PurchaseOrderDetail])
def get_purchase_order(
    po_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single purchase order by ID."""
    po = purchase_order_service.get_purchase_order(db, po_id)
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    
    return APIResponse(data=_po_to_detail(po))


@router.put("/{po_id}", response_model=APIResponse[PurchaseOrderDetail])
def update_purchase_order(
    request: Request,
    po_id: UUID,
    data: PurchaseOrderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a purchase order."""
    try:
        po = purchase_order_service.update_purchase_order(
            db=db,
            po_id=po_id,
            data=data,
            user_id=user.id,
            request=request,
        )
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        # Re-fetch with relationships
        po = purchase_order_service.get_purchase_order(db, po.id)
        
        return APIResponse(data=_po_to_detail(po))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    request: Request,
    po_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a purchase order (only in draft status)."""
    try:
        success = purchase_order_service.delete_purchase_order(
            db=db,
            po_id=po_id,
            user_id=user.id,
            request=request,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# STATUS OPERATIONS
# =============================================================================

@router.put("/{po_id}/status", response_model=APIResponse[PurchaseOrderDetail])
def update_purchase_order_status(
    request: Request,
    po_id: UUID,
    data: PurchaseOrderStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the status of a purchase order."""
    try:
        new_status = PurchaseOrderStatus(data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {data.status}",
        )
    
    try:
        po = purchase_order_service.update_status(
            db=db,
            po_id=po_id,
            new_status=new_status,
            user_id=user.id,
            notes=data.notes,
            request=request,
        )
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        # Re-fetch with relationships
        po = purchase_order_service.get_purchase_order(db, po.id)
        
        return APIResponse(data=_po_to_detail(po))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# RECEIVE OPERATIONS
# =============================================================================

@router.post("/{po_id}/receive", response_model=APIResponse[PurchaseOrderDetail])
def receive_items(
    request: Request,
    po_id: UUID,
    data: ReceiveItemsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive items on a purchase order."""
    try:
        po = purchase_order_service.receive_items(
            db=db,
            po_id=po_id,
            receive_data=data,
            user_id=user.id,
            request=request,
        )
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        # Re-fetch with relationships
        po = purchase_order_service.get_purchase_order(db, po.id)
        
        return APIResponse(data=_po_to_detail(po))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# LINE ITEM OPERATIONS
# =============================================================================

@router.post("/{po_id}/line-items", response_model=APIResponse[PurchaseOrderLineItemResponse], status_code=status.HTTP_201_CREATED)
def add_line_item(
    request: Request,
    po_id: UUID,
    data: PurchaseOrderLineItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a line item to a purchase order."""
    try:
        line_item = purchase_order_service.add_line_item(
            db=db,
            po_id=po_id,
            item_id=data.item_id,
            quantity=data.quantity_ordered,
            unit_price=data.unit_price,
            user_id=user.id,
            notes=data.notes,
            request=request,
        )
        
        if not line_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        return APIResponse(
            data=PurchaseOrderLineItemResponse(
                id=line_item.id,
                purchase_order_id=line_item.purchase_order_id,
                item_id=line_item.item_id,
                quantity_ordered=line_item.quantity_ordered,
                quantity_received=line_item.quantity_received,
                unit_price=line_item.unit_price,
                line_total=line_item.line_total,
                notes=line_item.notes,
                created_at=line_item.created_at,
                updated_at=line_item.updated_at,
                quantity_remaining=line_item.quantity_remaining,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{po_id}/line-items/{line_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_line_item(
    request: Request,
    po_id: UUID,
    line_item_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a line item from a purchase order."""
    try:
        success = purchase_order_service.remove_line_item(
            db=db,
            po_id=po_id,
            line_item_id=line_item_id,
            user_id=user.id,
            request=request,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line item not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# ITEM-SPECIFIC QUERIES
# =============================================================================

@router.get("/for-item/{item_id}", response_model=APIResponse[List[PurchaseOrderListItem]])
def get_purchase_orders_for_item(
    item_id: UUID,
    include_received: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all purchase orders containing a specific item."""
    purchase_orders = purchase_order_service.get_purchase_orders_for_item(
        db=db,
        item_id=item_id,
        include_received=include_received,
    )
    
    items = [_po_to_list_item(po) for po in purchase_orders]
    
    return APIResponse(data=items)
