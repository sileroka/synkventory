"""
Admin portal API endpoints.
These endpoints are for the admin.synkventory.com portal.
They provide cross-tenant management capabilities.
"""

import math
from datetime import datetime, date, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    get_password_hash,
    create_admin_access_token,
    decode_admin_token,
)
from app.db.session import get_db_no_tenant  # Admin endpoints don't use RLS
from app.models.admin_user import AdminUser
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog as AuditLogModel
from pydantic import BaseModel
from app.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantUserCreate,
    TenantUserUpdate,
    TenantUserResponse,
)

router = APIRouter()


# ----- Admin Authentication -----


def get_current_admin_user(
    request: Request,
    db: Session = Depends(get_db_no_tenant),
) -> AdminUser:
    """Get current admin user from cookie token."""
    token = request.cookies.get("admin_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_admin_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    admin_id = payload.get("admin_id")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    admin_user = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not admin_user or not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return admin_user


@router.post("/auth/login", response_model=AdminLoginResponse)
def admin_login(
    request: AdminLoginRequest,
    response: Response,
    db: Session = Depends(get_db_no_tenant),
):
    """Admin portal login."""
    admin_user = db.query(AdminUser).filter(AdminUser.email == request.email).first()

    if not admin_user or not verify_password(
        request.password, admin_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Update last login
    admin_user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create admin token
    token = create_admin_access_token(
        admin_id=str(admin_user.id),
        email=admin_user.email,
        is_super_admin=admin_user.is_super_admin,
    )

    # Set cookie
    response.set_cookie(
        key="admin_access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24,  # 24 hours
    )

    return AdminLoginResponse(user=AdminUserResponse.model_validate(admin_user))


@router.post("/auth/logout")
def admin_logout(response: Response):
    """Admin portal logout."""
    response.delete_cookie("admin_access_token")
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=AdminUserResponse)
def get_current_admin(
    admin_user: AdminUser = Depends(get_current_admin_user),
):
    """Get current admin user info."""
    return AdminUserResponse.model_validate(admin_user)


# ----- Admin User Management -----


@router.get("/admin-users", response_model=List[AdminUserResponse])
def list_admin_users(
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """List all admin users. Requires super admin."""
    if not admin_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    users = db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()
    return [AdminUserResponse.model_validate(u) for u in users]


@router.post(
    "/admin-users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_user(
    data: AdminUserCreate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Create a new admin user. Requires super admin."""
    if not admin_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    # Check if email exists
    existing = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_admin = AdminUser(
        email=data.email,
        name=data.name,
        password_hash=get_password_hash(data.password),
        is_super_admin=data.is_super_admin,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return AdminUserResponse.model_validate(new_admin)


@router.patch("/admin-users/{admin_id}", response_model=AdminUserResponse)
def update_admin_user(
    admin_id: UUID,
    data: AdminUserUpdate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Update an admin user. Requires super admin."""
    if not admin_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    target_admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )

    # Update fields if provided
    if data.name is not None:
        target_admin.name = data.name
    if data.is_super_admin is not None:
        target_admin.is_super_admin = data.is_super_admin
    if data.is_active is not None:
        target_admin.is_active = data.is_active

    db.commit()
    db.refresh(target_admin)

    return AdminUserResponse.model_validate(target_admin)


# ----- Tenant Management -----


@router.get("/tenants", response_model=List[TenantResponse])
def list_tenants(
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """List all tenants with user counts."""
    # Query tenants with user count
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()

    result = []
    for tenant in tenants:
        user_count = (
            db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar()
        )
        tenant_dict = {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at,
            "updated_at": tenant.updated_at,
            "user_count": user_count or 0,
        }
        result.append(TenantResponse.model_validate(tenant_dict))

    return result


@router.post(
    "/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED
)
def create_tenant(
    data: TenantCreate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Create a new tenant."""
    # Check if slug exists
    existing = db.query(Tenant).filter(Tenant.slug == data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already exists",
        )

    tenant = Tenant(
        name=data.name,
        slug=data.slug,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        user_count=0,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: UUID,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Get a specific tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    user_count = (
        db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar()
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        user_count=user_count or 0,
    )


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: UUID,
    data: TenantUpdate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Update a tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if data.name is not None:
        tenant.name = data.name
    if data.is_active is not None:
        tenant.is_active = data.is_active

    db.commit()
    db.refresh(tenant)

    user_count = (
        db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar()
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        user_count=user_count or 0,
    )


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: UUID,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Delete a tenant. Requires super admin."""
    if not admin_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    db.delete(tenant)
    db.commit()


# ----- Tenant User Management -----


@router.get("/tenants/{tenant_id}/users", response_model=List[TenantUserResponse])
def list_tenant_users(
    tenant_id: UUID,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """List all users in a tenant."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    users = (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [TenantUserResponse.model_validate(u) for u in users]


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=TenantUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_user(
    tenant_id: UUID,
    data: TenantUserCreate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Create a user in a tenant."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Check if email exists in this tenant
    existing = (
        db.query(User)
        .filter(
            User.tenant_id == tenant_id,
            User.email == data.email,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this tenant",
        )

    user = User(
        tenant_id=tenant_id,
        email=data.email,
        name=data.name,
        password_hash=get_password_hash(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TenantUserResponse.model_validate(user)


@router.get("/tenants/{tenant_id}/users/{user_id}", response_model=TenantUserResponse)
def get_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Get a specific user in a tenant."""
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return TenantUserResponse.model_validate(user)


@router.patch("/tenants/{tenant_id}/users/{user_id}", response_model=TenantUserResponse)
def update_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    data: TenantUserUpdate,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Update a user in a tenant."""
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return TenantUserResponse.model_validate(user)


@router.delete(
    "/tenants/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Delete a user in a tenant."""
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()


# ----- Audit Logs (Cross-Tenant) -----


class AdminAuditLogResponse(BaseModel):
    """Admin audit log response with tenant info."""

    id: UUID
    tenant_id: UUID
    tenant_name: Optional[str] = None
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None
    extra_data: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminAuditLogListResponse(BaseModel):
    """Paginated audit log response."""

    data: List[AdminAuditLogResponse]
    meta: dict


@router.get("/audit-logs", response_model=AdminAuditLogListResponse)
def list_admin_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        50, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    tenant_id: Optional[UUID] = Query(
        None, alias="tenantId", description="Filter by tenant"
    ),
    user_id: Optional[UUID] = Query(None, alias="userId", description="Filter by user"),
    action: Optional[str] = Query(
        None, description="Filter by action type (LOGIN, LOGOUT, etc.)"
    ),
    entity_type: Optional[str] = Query(
        None, alias="entityType", description="Filter by entity type"
    ),
    start_date: Optional[date] = Query(
        None, alias="startDate", description="Filter from this date"
    ),
    end_date: Optional[date] = Query(
        None, alias="endDate", description="Filter until this date"
    ),
    search: Optional[str] = Query(
        None, description="Search in user email or entity name"
    ),
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """
    Get audit logs across all tenants (admin access only).

    Supports filtering by tenant, user, action type, date range, and search.
    """
    query = db.query(AuditLogModel)

    # Apply filters
    if tenant_id:
        query = query.filter(AuditLogModel.tenant_id == tenant_id)
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    if action:
        query = query.filter(AuditLogModel.action == action)
    if entity_type:
        query = query.filter(AuditLogModel.entity_type == entity_type)
    if start_date:
        query = query.filter(
            AuditLogModel.created_at
            >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query = query.filter(
            AuditLogModel.created_at <= datetime.combine(end_date, datetime.max.time())
        )
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (AuditLogModel.user_email.ilike(search_term))
            | (AuditLogModel.entity_name.ilike(search_term))
        )

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Apply pagination and ordering
    skip = (page - 1) * page_size
    logs = (
        query.order_by(desc(AuditLogModel.created_at))
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Get tenant names for the logs
    tenant_ids = list(set(log.tenant_id for log in logs if log.tenant_id))
    tenant_names = {}
    if tenant_ids:
        tenants = db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()
        tenant_names = {t.id: t.name for t in tenants}

    # Build response
    data = []
    for log in logs:
        data.append(
            AdminAuditLogResponse(
                id=log.id,
                tenant_id=log.tenant_id,
                tenant_name=tenant_names.get(log.tenant_id),
                user_id=log.user_id,
                user_email=log.user_email,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                entity_name=log.entity_name,
                extra_data=log.extra_data,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
        )

    return AdminAuditLogListResponse(
        data=data,
        meta={
            "page": page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
        },
    )


@router.get("/audit-logs/actions", response_model=List[str])
def list_audit_actions(
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Get list of distinct action types in audit logs."""
    results = db.query(AuditLogModel.action).distinct().all()
    return sorted([r[0] for r in results if r[0]])


@router.get("/audit-logs/entity-types", response_model=List[str])
def list_entity_types(
    admin_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db_no_tenant),
):
    """Get list of distinct entity types in audit logs."""
    results = db.query(AuditLogModel.entity_type).distinct().all()
    return sorted([r[0] for r in results if r[0]])
