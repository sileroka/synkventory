"""
Category attributes API endpoints for managing custom fields per category.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.category import Category
from app.models.category_attribute import CategoryAttribute as CategoryAttributeModel
from app.schemas.category_attribute import (
    CategoryAttribute,
    CategoryAttributeCreate,
    CategoryAttributeUpdate,
    CategoryAttributeReorder,
)

router = APIRouter()


@router.get(
    "/categories/{category_id}/attributes", response_model=List[CategoryAttribute]
)
def get_category_attributes(
    category_id: UUID,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get all attributes defined for a category.
    Returns attributes ordered by display_order.
    """
    # Verify category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    query = db.query(CategoryAttributeModel).filter(
        CategoryAttributeModel.category_id == category_id
    )

    if not include_inactive:
        query = query.filter(CategoryAttributeModel.is_active == True)

    attributes = query.order_by(asc(CategoryAttributeModel.display_order)).all()
    return attributes


@router.post(
    "/categories/{category_id}/attributes",
    response_model=CategoryAttribute,
    status_code=status.HTTP_201_CREATED,
)
def create_category_attribute(
    category_id: UUID,
    data: CategoryAttributeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new attribute for a category.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required",
        )

    # Verify category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check for duplicate key
    existing = (
        db.query(CategoryAttributeModel)
        .filter(
            CategoryAttributeModel.category_id == category_id,
            CategoryAttributeModel.key == data.key,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attribute with key '{data.key}' already exists for this category",
        )

    # Get max display_order
    max_order = (
        db.query(CategoryAttributeModel.display_order)
        .filter(CategoryAttributeModel.category_id == category_id)
        .order_by(CategoryAttributeModel.display_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 0

    attribute = CategoryAttributeModel(
        tenant_id=tenant.id,
        category_id=category_id,
        name=data.name,
        key=data.key,
        attribute_type=data.attribute_type.value,
        description=data.description,
        options=data.options,
        is_required=data.is_required,
        default_value=data.default_value,
        display_order=data.display_order if data.display_order > 0 else next_order,
        created_by=user.id,
    )

    db.add(attribute)
    db.commit()
    db.refresh(attribute)

    return attribute


@router.get("/attributes/{attribute_id}", response_model=CategoryAttribute)
def get_attribute(
    attribute_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific attribute by ID."""
    attribute = (
        db.query(CategoryAttributeModel)
        .filter(CategoryAttributeModel.id == attribute_id)
        .first()
    )
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    return attribute


@router.patch("/attributes/{attribute_id}", response_model=CategoryAttribute)
def update_attribute(
    attribute_id: UUID,
    data: CategoryAttributeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an attribute."""
    attribute = (
        db.query(CategoryAttributeModel)
        .filter(CategoryAttributeModel.id == attribute_id)
        .first()
    )
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attribute, field, value)

    attribute.updated_by = user.id

    db.commit()
    db.refresh(attribute)

    return attribute


@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(
    attribute_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete an attribute.
    Note: This doesn't remove the values from existing items,
    they just won't be displayed/editable anymore.
    """
    attribute = (
        db.query(CategoryAttributeModel)
        .filter(CategoryAttributeModel.id == attribute_id)
        .first()
    )
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )

    db.delete(attribute)
    db.commit()


@router.post("/categories/{category_id}/attributes/reorder")
def reorder_attributes(
    category_id: UUID,
    data: CategoryAttributeReorder,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reorder attributes by providing an ordered list of attribute IDs."""
    # Verify category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Update display_order for each attribute
    for index, attr_id in enumerate(data.attribute_ids):
        attribute = (
            db.query(CategoryAttributeModel)
            .filter(
                CategoryAttributeModel.id == attr_id,
                CategoryAttributeModel.category_id == category_id,
            )
            .first()
        )
        if attribute:
            attribute.display_order = index
            attribute.updated_by = user.id

    db.commit()

    return {"message": "Attributes reordered successfully"}
