"""
Authentication API endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_token_pair,
    decode_token,
    is_refresh_token,
    verify_password,
    get_password_hash,
)
from app.core.tenant import get_current_tenant
from app.db.session import get_db
from app.models.user import User
from app.services.audit import audit_service
from app.models.audit_log import AuditAction, EntityType

logger = logging.getLogger(__name__)

router = APIRouter()


def set_auth_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """Set an authentication cookie with proper domain settings."""
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=True,  # Requires HTTPS in production
        samesite="lax",
        max_age=max_age,
        domain=settings.COOKIE_DOMAIN,  # None in dev, ".synkventory.com" in prod
    )


# =============================================================================
# SCHEMAS
# =============================================================================


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserResponse
    message: str = "Login successful"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/auth/login", response_model=LoginResponse)
def login(
    login_request: LoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and set JWT cookies.

    SECURITY: Always returns generic error message to prevent user enumeration.
    """
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    # Must have tenant context
    tenant = get_current_tenant()
    if not tenant:
        raise auth_error

    # Find user by email AND tenant_id
    user = (
        db.query(User)
        .filter(User.email == login_request.email, User.tenant_id == tenant.id)
        .first()
    )

    # User not found - still verify to prevent timing attacks
    if not user:
        verify_password(
            login_request.password, "$2b$12$dummy_hash_to_prevent_timing_attacks"
        )
        # Log failed login attempt (no user context)
        audit_service.log(
            db=db,
            tenant_id=tenant.id,
            user_id=None,
            action=AuditAction.LOGIN_FAILED,
            entity_type=EntityType.USER,
            entity_id=None,
            extra_data={
                "email": login_request.email,
                "reason": "user_not_found",
            },
            request=http_request,
        )
        raise auth_error

    # Check if user is active
    if not user.is_active:
        audit_service.log(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            action=AuditAction.LOGIN_FAILED,
            entity_type=EntityType.USER,
            entity_id=user.id,
            extra_data={"reason": "user_inactive"},
            request=http_request,
        )
        raise auth_error

    # Check if user is locked
    if user.is_locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            audit_service.log(
                db=db,
                tenant_id=tenant.id,
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                entity_type=EntityType.USER,
                entity_id=user.id,
                extra_data={"reason": "user_locked"},
                request=http_request,
            )
            raise auth_error

    # Verify password
    if not verify_password(login_request.password, user.password_hash):
        audit_service.log(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            action=AuditAction.LOGIN_FAILED,
            entity_type=EntityType.USER,
            entity_id=user.id,
            extra_data={"reason": "invalid_password"},
            request=http_request,
        )
        raise auth_error

    # Create tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
    )

    # Capture user data BEFORE any audit logging that might rollback
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
    )

    # Set HttpOnly cookies
    set_auth_cookie(response, "access_token", tokens.access_token, 30 * 60)  # 30 min
    set_auth_cookie(
        response, "refresh_token", tokens.refresh_token, 7 * 24 * 60 * 60
    )  # 7 days

    # Log successful login (non-critical - don't fail login if audit fails)
    try:
        audit_service.log_login(
            db=db,
            tenant_id=tenant.id,
            user_id=UUID(user_response.id),
            request=http_request,
        )
    except Exception as e:
        logger.warning(f"Failed to log login audit: {e}")

    return LoginResponse(user=user_response)


@router.post("/auth/refresh")
def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    Implements refresh token rotation for security.
    """
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )

    if not refresh_token:
        raise auth_error

    # Verify it's actually a refresh token
    if not is_refresh_token(refresh_token):
        raise auth_error

    # Decode token
    token_data = decode_token(refresh_token)
    if not token_data:
        raise auth_error

    # Verify token hasn't expired
    if token_data.exp < datetime.now(timezone.utc):
        raise auth_error

    # Verify tenant context matches
    tenant = get_current_tenant()
    if not tenant or str(tenant.id) != token_data.tenant_id:
        raise auth_error

    # Verify user still exists and is active
    user = db.query(User).filter(User.id == UUID(token_data.user_id)).first()

    if not user or not user.is_active:
        raise auth_error

    # Create new token pair (rotation)
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
    )

    # Set new cookies
    set_auth_cookie(response, "access_token", tokens.access_token, 30 * 60)
    set_auth_cookie(response, "refresh_token", tokens.refresh_token, 7 * 24 * 60 * 60)

    return {"message": "Tokens refreshed"}


def delete_auth_cookie(response: Response, key: str) -> None:
    """Delete an authentication cookie with proper domain settings."""
    response.delete_cookie(
        key=key,
        domain=settings.COOKIE_DOMAIN,
    )


@router.post("/auth/logout")
def logout(
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Clear auth cookies and log the logout."""
    tenant = get_current_tenant()

    # Log logout before clearing cookies
    if tenant and user:
        audit_service.log_logout(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            request=http_request,
        )

    delete_auth_cookie(response, "access_token")
    delete_auth_cookie(response, "refresh_token")
    return {"message": "Logged out"}


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "data": UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
        )
    }


@router.post("/auth/register", response_model=LoginResponse, status_code=201)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Register a new user for the current tenant.
    Auto-logs in after registration.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # Check if email already exists for this tenant
    existing = (
        db.query(User)
        .filter(User.email == request.email, User.tenant_id == tenant.id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-login: create tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
    )

    # Set cookies
    set_auth_cookie(response, "access_token", tokens.access_token, 30 * 60)
    set_auth_cookie(response, "refresh_token", tokens.refresh_token, 7 * 24 * 60 * 60)

    return LoginResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
        ),
        message="Registration successful",
    )
