"""
User management API endpoints.
"""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_manager_or_admin
from app.core.security import get_password_hash, verify_password
from app.core.tenant import get_current_tenant
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    PasswordChange,
    PasswordReset,
    User as UserSchema,
    UserCreate,
    UserListResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    List all users in the tenant with pagination and filtering.
    Requires manager or admin role.
    """
    query = db.query(User)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if role:
        query = query.filter(User.role == role)

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Get paginated results
    users = query.order_by(User.name).offset(offset).limit(page_size).all()

    return UserListResponse(
        items=[UserSchema.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new user in the tenant.
    Requires manager or admin role.
    Managers cannot create admins.
    """
    tenant = get_current_tenant()

    # Check if email already exists in tenant
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Managers cannot create admins
    if current_user.role == UserRole.MANAGER.value and user_data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot create admin users",
        )

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's information."""
    return UserSchema.model_validate(current_user)


@router.put("/me/password")
def change_own_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: UUID,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Get a specific user by ID.
    Requires manager or admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserSchema.model_validate(user)


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Update a user.
    Requires manager or admin role.
    Managers cannot modify admins or promote users to admin.
    Users cannot deactivate themselves.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Managers cannot modify admins
    if (
        current_user.role == UserRole.MANAGER.value
        and user.role == UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot modify admin users",
        )

    # Managers cannot promote to admin
    if current_user.role == UserRole.MANAGER.value and user_data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot promote users to admin",
        )

    # Users cannot deactivate themselves
    if user_id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    # Update fields
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.role is not None:
        user.role = user_data.role.value
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
        # Unlock user when activating
        if user_data.is_active:
            user.is_locked = False
            user.locked_until = None

    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserSchema)
def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Activate a user and unlock them.
    Requires manager or admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Managers cannot modify admins
    if (
        current_user.role == UserRole.MANAGER.value
        and user.role == UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot modify admin users",
        )

    user.is_active = True
    user.is_locked = False
    user.locked_until = None
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserSchema)
def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Deactivate a user.
    Requires manager or admin role.
    Users cannot deactivate themselves.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot deactivate yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    # Managers cannot modify admins
    if (
        current_user.role == UserRole.MANAGER.value
        and user.role == UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot modify admin users",
        )

    user.is_active = False
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: UUID,
    password_data: PasswordReset,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Reset a user's password.
    Requires manager or admin role.
    Managers cannot reset admin passwords.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Managers cannot reset admin passwords
    if (
        current_user.role == UserRole.MANAGER.value
        and user.role == UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot reset admin passwords",
        )

    user.password_hash = get_password_hash(password_data.new_password)
    # Unlock user after password reset
    user.is_locked = False
    user.locked_until = None
    db.commit()

    return {"message": "Password reset successfully"}
