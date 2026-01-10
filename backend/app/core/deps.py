"""
Authentication dependencies for FastAPI routes.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.core.tenant import get_current_tenant, TenantContext
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.

    Usage:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.email}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",  # Generic error
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    # Decode token
    token_data = decode_token(access_token)
    if not token_data:
        raise credentials_exception

    # Verify token hasn't expired
    if token_data.exp < datetime.now(timezone.utc):
        raise credentials_exception

    # Verify tenant context matches token
    tenant = get_current_tenant()
    if not tenant or str(tenant.id) != token_data.tenant_id:
        raise credentials_exception

    # Get user from database
    # Compare using string ID to work across PostgreSQL (UUID) and SQLite tests (String)
    user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise credentials_exception

    # Check if user is locked
    if user.is_locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise credentials_exception

    return user


def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures user is active."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user


def require_tenant() -> TenantContext:
    """
    Dependency that ensures a valid tenant context exists.
    Use for routes that must have tenant context but don't require auth.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    return tenant


def require_role(*allowed_roles: str):
    """
    Dependency factory that ensures the current user has one of the allowed roles.

    Usage:
        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_role("admin"))):
            return {"user": user.email}

        @router.get("/manager-or-admin")
        def manager_route(user: User = Depends(require_role("manager", "admin"))):
            return {"user": user.email}
    """

    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_checker


def require_manager_or_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures user is a manager or admin."""
    if user.role not in ("manager", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures user is an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user
