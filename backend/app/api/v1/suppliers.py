"""
API endpoints for Supplier management.
"""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.schemas.response import DataResponse, ListResponse, PaginationMeta, MessageResponse
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.services.supplier_service import supplier_service

router = APIRouter(prefix="/suppliers", dependencies=[Depends(get_current_user)])


def _to_response(supplier) -> SupplierResponse:
    purchase_order_ids = [po.id for po in getattr(supplier, "purchase_orders", [])]
    return SupplierResponse.model_validate(
        supplier,
        update={"purchase_order_ids": purchase_order_ids},
    )


@router.get("/", response_model=ListResponse[SupplierResponse])
def list_suppliers(
    search: Optional[str] = Query(None, description="Search suppliers by name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    suppliers, total = supplier_service.get_suppliers(
        db=db,
        tenant_id=tenant.id,
        search=search,
        page=page,
        page_size=page_size,
    )

    data = [_to_response(s) for s in suppliers]
    total_pages = math.ceil(total / page_size) if page_size else 0
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
    )
    return ListResponse(data=data, meta=meta)


@router.post("/", response_model=DataResponse[SupplierResponse], status_code=status.HTTP_201_CREATED)
def create_supplier_endpoint(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    supplier = supplier_service.create_supplier(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        **payload.model_dump(),
    )
    db.commit()
    db.refresh(supplier)

    return DataResponse(data=_to_response(supplier))


@router.get("/{supplier_id}", response_model=DataResponse[SupplierResponse])
def get_supplier_endpoint(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    supplier = supplier_service.get_supplier(db=db, tenant_id=tenant.id, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    return DataResponse(data=_to_response(supplier))


@router.put("/{supplier_id}", response_model=DataResponse[SupplierResponse])
@router.patch("/{supplier_id}", response_model=DataResponse[SupplierResponse])
def update_supplier_endpoint(
    supplier_id: UUID,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    supplier = supplier_service.update_supplier(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        supplier_id=supplier_id,
        **payload.model_dump(exclude_unset=True),
    )
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    db.commit()
    db.refresh(supplier)
    return DataResponse(data=_to_response(supplier))


@router.delete("/{supplier_id}", response_model=MessageResponse)
def delete_supplier_endpoint(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    supplier = supplier_service.get_supplier(db=db, tenant_id=tenant.id, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    deleted = supplier_service.delete_supplier(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        supplier_id=supplier_id,
    )
    db.commit()

    message = (
        "Supplier deleted"
        if deleted
        else "Supplier deactivated because it is referenced by purchase orders"
    )
    return MessageResponse(message=message)
