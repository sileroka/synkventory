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
    user = db.query(User).filter(User.id == UUID(token_data.user_id)).first()
    
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
