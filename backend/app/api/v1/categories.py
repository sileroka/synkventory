import math
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.category import Category as CategoryModel
from app.models.audit_log import AuditAction, EntityType
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryTreeNode,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
    MessageResponse,
)
from app.services.audit import audit_service

# All routes in this router require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


def build_category_tree(
    categories: List[CategoryModel], parent_id: UUID = None
) -> List[dict]:
    """Build a hierarchical tree structure from flat category list."""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            node = {
                "id": str(category.id),
                "name": category.name,
                "code": category.code,
                "description": category.description,
                "parentId": str(category.parent_id) if category.parent_id else None,
                "isActive": category.is_active,
                "createdAt": (
                    category.created_at.isoformat() if category.created_at else None
                ),
                "updatedAt": (
                    category.updated_at.isoformat() if category.updated_at else None
                ),
                "children": children,
            }
            tree.append(node)
    return tree


@router.get("", response_model=ListResponse[Category], response_model_by_alias=True)
def get_categories(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=1000, alias="pageSize", description="Items per page"
    ),
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
    ),
    parent_id: str = Query(None, alias="parentId", description="Filter by parent ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve categories with pagination.
    """
    query = db.query(CategoryModel)

    # Apply filters
    if is_active is not None:
        query = query.filter(CategoryModel.is_active == is_active)
    if parent_id is not None:
        if parent_id == "null" or parent_id == "":
            query = query.filter(CategoryModel.parent_id.is_(None))
        else:
            query = query.filter(CategoryModel.parent_id == parent_id)

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get items
    categories = query.offset(skip).limit(page_size).all()

    return ListResponse(
        data=categories,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/tree", response_model=DataResponse[List[dict]], response_model_by_alias=True
)
def get_category_tree(
    request: Request,
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve categories as a hierarchical tree structure.
    """
    query = db.query(CategoryModel)

    if is_active is not None:
        query = query.filter(CategoryModel.is_active == is_active)

    categories = query.all()
    tree = build_category_tree(categories, None)

    return DataResponse(data=tree, meta=get_response_meta(request))


@router.get(
    "/{category_id}",
    response_model=DataResponse[Category],
    response_model_by_alias=True,
)
def get_category(category_id: UUID, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific category by ID.
    """
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return DataResponse(data=category, meta=get_response_meta(request))


@router.post(
    "",
    response_model=DataResponse[Category],
    status_code=201,
    response_model_by_alias=True,
)
def create_category(
    category: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new category.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Check if code already exists
    existing_category = (
        db.query(CategoryModel).filter(CategoryModel.code == category.code).first()
    )
    if existing_category:
        raise HTTPException(status_code=400, detail="Category code already exists")

    # Validate parent_id if provided
    if category.parent_id:
        parent = (
            db.query(CategoryModel)
            .filter(CategoryModel.id == category.parent_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")

    # Create category with tenant_id from context
    db_category = CategoryModel(
        **category.model_dump(),
        tenant_id=tenant.id,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    # Log the creation
    if tenant:
        audit_service.log_create(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            entity_type=EntityType.CATEGORY,
            entity_id=db_category.id,
            entity_name=f"{db_category.code} - {db_category.name}",
            data=category.model_dump(),
            request=request,
        )

    return DataResponse(data=db_category, meta=get_response_meta(request))


@router.put(
    "/{category_id}",
    response_model=DataResponse[Category],
    response_model_by_alias=True,
)
def update_category(
    category_id: UUID,
    category: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update a category.
    """
    tenant = get_current_tenant()

    db_category = (
        db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture old values for audit
    old_values = {
        "name": db_category.name,
        "code": db_category.code,
        "description": db_category.description,
        "is_active": db_category.is_active,
        "parent_id": str(db_category.parent_id) if db_category.parent_id else None,
    }

    update_data = category.model_dump(exclude_unset=True)

    # Check if new code conflicts with existing
    if "code" in update_data and update_data["code"] != db_category.code:
        existing = (
            db.query(CategoryModel)
            .filter(CategoryModel.code == update_data["code"])
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Category code already exists")

    # Validate parent_id if provided
    if "parent_id" in update_data and update_data["parent_id"]:
        # Prevent setting self as parent
        if str(category_id) == update_data["parent_id"]:
            raise HTTPException(
                status_code=400, detail="Category cannot be its own parent"
            )
        parent = (
            db.query(CategoryModel)
            .filter(CategoryModel.id == update_data["parent_id"])
            .first()
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")

    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)

    # Log the update with changes
    if tenant:
        changes = {}
        for field, new_value in update_data.items():
            old_value = old_values.get(field)
            if hasattr(new_value, "hex"):
                new_value = str(new_value)
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}

        if changes:
            audit_service.log_update(
                db=db,
                tenant_id=tenant.id,
                user_id=user.id,
                entity_type=EntityType.CATEGORY,
                entity_id=db_category.id,
                entity_name=f"{db_category.code} - {db_category.name}",
                changes=changes,
                request=request,
            )

    return DataResponse(data=db_category, meta=get_response_meta(request))


@router.delete(
    "/{category_id}", response_model=MessageResponse, response_model_by_alias=True
)
def delete_category(
    category_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a category.
    """
    tenant = get_current_tenant()

    db_category = (
        db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture category info for audit
    category_name = f"{db_category.code} - {db_category.name}"
    category_data = {
        "code": db_category.code,
        "name": db_category.name,
    }

    # Check for children
    children = (
        db.query(CategoryModel).filter(CategoryModel.parent_id == category_id).count()
    )
    if children > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with child categories. Delete children first.",
        )

    db.delete(db_category)
    db.commit()

    # Log the deletion
    if tenant:
        audit_service.log_delete(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            entity_type=EntityType.CATEGORY,
            entity_id=category_id,
            entity_name=category_name,
            data=category_data,
            request=request,
        )

    return MessageResponse(
        message="Category deleted successfully", meta=get_response_meta(request)
    )
