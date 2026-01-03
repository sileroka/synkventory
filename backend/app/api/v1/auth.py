"""
Authentication API endpoints.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

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

router = APIRouter()


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
    request: LoginRequest,
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
        .filter(User.email == request.email, User.tenant_id == tenant.id)
        .first()
    )

    # User not found - still verify to prevent timing attacks
    if not user:
        verify_password(request.password, "$2b$12$dummy_hash_to_prevent_timing_attacks")
        raise auth_error

    # Check if user is active
    if not user.is_active:
        raise auth_error

    # Check if user is locked
    if user.is_locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise auth_error

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise auth_error

    # Create tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
    )

    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,  # Requires HTTPS in production
        samesite="lax",
        max_age=30 * 60,  # 30 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return LoginResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
        )
    )


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
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return {"message": "Tokens refreshed"}


@router.post("/auth/logout")
def logout(response: Response):
    """Clear auth cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "data": UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
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
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return LoginResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
        ),
        message="Registration successful",
    )
