"""
API endpoints for Customer management.
"""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    MessageResponse,
)
from app.services.customer_service import customer_service

router = APIRouter(prefix="/customers", dependencies=[Depends(get_current_user)])


@router.get("/")
def list_customers(
    search: Optional[str] = Query(None, description="Search customers by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    customers, total = customer_service.get_customers(
        db=db,
        tenant_id=tenant.id,
        search=search,
        page=page,
        page_size=page_size,
    )

    items = [CustomerResponse.model_validate(c) for c in customers]
    # Align with tests expecting data.items and data.total
    return {
        "data": {
            "items": [i.model_dump(by_alias=True) for i in items],
            "total": total,
        },
        "meta": {
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }


@router.post("/", response_model=DataResponse[CustomerResponse], status_code=status.HTTP_201_CREATED)
def create_customer_endpoint(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    customer = customer_service.create_customer(
        db=db,
        user_id=user.id,
        **payload.model_dump(),
    )
    db.commit()
    db.refresh(customer)

    return DataResponse(data=CustomerResponse.model_validate(customer))


@router.get("/{customer_id}", response_model=DataResponse[CustomerResponse])
def get_customer_endpoint(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    customer = customer_service.get_customer(db=db, tenant_id=tenant.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return DataResponse(data=CustomerResponse.model_validate(customer))


@router.put("/{customer_id}", response_model=DataResponse[CustomerResponse])
@router.patch("/{customer_id}", response_model=DataResponse[CustomerResponse])
def update_customer_endpoint(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    customer = customer_service.update_customer(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        customer_id=customer_id,
        **payload.model_dump(exclude_unset=True),
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    db.commit()
    db.refresh(customer)
    return DataResponse(data=CustomerResponse.model_validate(customer))


@router.delete("/{customer_id}", response_model=MessageResponse)
def delete_customer_endpoint(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not found")

    customer = customer_service.get_customer(db=db, tenant_id=tenant.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    deleted = customer_service.delete_customer(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        customer_id=customer_id,
    )
    db.commit()

    message = (
        "Customer deleted" if deleted else "Customer deactivated"
    )
    return MessageResponse(message=message)
