"""
API endpoints for Sales Orders.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.sales_order import SalesOrderStatus, SalesOrderPriority
from app.models.user import User
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderResponse,
    SalesOrderListItem,
    SalesOrderDetail,
    SalesOrderStatusUpdate,
    SalesOrderLineItemResponse,
    SalesOrderLineItemCreate,
)
from app.schemas.response import PaginatedResponse, APIResponse
from app.services.sales_order_service import sales_order_service

router = APIRouter(prefix="/sales-orders", dependencies=[Depends(get_current_user)])


def _so_to_list_item(so) -> SalesOrderListItem:
    item_count = len(so.line_items) if hasattr(so, "line_items") and so.line_items else 0
    items_shipped = sum(
        1 for li in (so.line_items or []) if li.quantity_shipped >= li.quantity_ordered
    ) if hasattr(so, "line_items") and so.line_items else 0

    return SalesOrderListItem(
        id=so.id,
        order_number=so.order_number,
        customer_id=so.customer_id,
        status=so.status.value if hasattr(so.status, "value") else so.status,
        priority=so.priority.value if hasattr(so.priority, "value") else so.priority,
        total_amount=so.total_amount,
        order_date=so.order_date,
        expected_ship_date=so.expected_ship_date,
        shipped_date=so.shipped_date,
        created_at=so.created_at,
        item_count=item_count,
        items_shipped=items_shipped,
        customer=so.customer if hasattr(so, "customer") else None,
        is_overdue=(False if not so.expected_ship_date else (so.status.value not in ["shipped", "cancelled"])),
    )


def _so_to_detail(so) -> SalesOrderDetail:
    line_items = []
    for li in (so.line_items or []):
        line_items.append(
            SalesOrderLineItemResponse(
                id=li.id,
                sales_order_id=li.sales_order_id,
                item_id=li.item_id,
                quantity_ordered=li.quantity_ordered,
                quantity_shipped=li.quantity_shipped,
                unit_price=li.unit_price,
                line_total=li.line_total,
                notes=li.notes,
                created_at=li.created_at,
                updated_at=li.updated_at,
                quantity_remaining=max(0, li.quantity_ordered - li.quantity_shipped),
            )
        )

    # Recompute subtotal and total to avoid cross-dialect numeric quirks in tests
    from decimal import Decimal
    computed_subtotal = sum(
        (Decimal(str(li.quantity_ordered)) * (li.unit_price or Decimal("0")))
        for li in (so.line_items or [])
    )
    computed_total = computed_subtotal + (so.tax_amount or 0) + (so.shipping_cost or 0)

    return SalesOrderDetail(
        id=so.id,
        tenant_id=so.tenant_id,
        order_number=so.order_number,
        customer_id=so.customer_id,
        status=so.status.value if hasattr(so.status, "value") else so.status,
        priority=so.priority.value if hasattr(so.priority, "value") else so.priority,
        order_date=so.order_date,
        expected_ship_date=so.expected_ship_date,
        shipped_date=so.shipped_date,
        cancelled_date=so.cancelled_date,
        notes=so.notes,
        subtotal=computed_subtotal,
        tax_amount=so.tax_amount,
        shipping_cost=so.shipping_cost,
        total_amount=computed_total,
        created_at=so.created_at,
        updated_at=so.updated_at,
        created_by=so.created_by,
        line_items=line_items,
        customer=so.customer if hasattr(so, "customer") else None,
        customer_name=so.customer.name if so.customer else None,
        is_overdue=(False if not so.expected_ship_date else (so.status.value not in ["shipped", "cancelled"])),
    )


@router.get("/")
def list_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status_enum = None
    if status:
        try:
            status_enum = SalesOrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}")

    priority_enum = None
    if priority:
        try:
            priority_enum = SalesOrderPriority(priority)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid priority: {priority}")

    sales_orders, total = sales_order_service.get_sales_orders(
        db=db,
        page=page,
        page_size=page_size,
        status=status_enum,
        priority=priority_enum,
        customer_id=customer_id,
    )

    items = [_so_to_list_item(so) for so in sales_orders]

    # Align with tests expecting data.totalItems inside data
    return {
        "data": {
            "items": [i.model_dump(by_alias=True) for i in items],
            "totalItems": total,
        },
        "meta": {
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": (total + page_size - 1) // page_size,
        },
    }


@router.post("/", response_model=APIResponse[SalesOrderDetail], status_code=status.HTTP_201_CREATED)
@router.post("", response_model=APIResponse[SalesOrderDetail], status_code=status.HTTP_201_CREATED)
def create_sales_order(
    request: Request,
    data: SalesOrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        so = sales_order_service.create_sales_order(db=db, data=data, user_id=user.id, request=request)
        so = sales_order_service.get_sales_order(db, so.id)
        return APIResponse(data=_so_to_detail(so))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{so_id}", response_model=APIResponse[SalesOrderDetail])
def get_sales_order(
    so_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    so = sales_order_service.get_sales_order(db, so_id)
    if not so:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
    return APIResponse(data=_so_to_detail(so))


@router.put("/{so_id}", response_model=APIResponse[SalesOrderDetail])
def update_sales_order(
    request: Request,
    so_id: UUID,
    data: SalesOrderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        so = sales_order_service.update_sales_order(db=db, so_id=so_id, data=data, user_id=user.id, request=request)
        if not so:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
        so = sales_order_service.get_sales_order(db, so.id)
        return APIResponse(data=_so_to_detail(so))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{so_id}/status", response_model=APIResponse[SalesOrderDetail])
def update_sales_order_status(
    request: Request,
    so_id: UUID,
    data: SalesOrderStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        new_status = SalesOrderStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {data.status}")

    try:
        so = sales_order_service.update_status(
            db=db,
            so_id=so_id,
            new_status=new_status,
            user_id=user.id,
            notes=data.notes,
            request=request,
        )
        if not so:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
        so = sales_order_service.get_sales_order(db, so.id)
        return APIResponse(data=_so_to_detail(so))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
