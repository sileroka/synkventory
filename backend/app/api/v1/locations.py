import math
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User
from app.models.location import Location as LocationModel, LocationType
from app.models.audit_log import AuditAction, EntityType
from app.schemas.location import (
    Location,
    LocationCreate,
    LocationUpdate,
    LocationTreeNode,
    LocationTypeInfo,
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


def build_location_tree(
    locations: List[LocationModel], parent_id: UUID = None
) -> List[dict]:
    """Build a hierarchical tree structure from flat location list."""
    tree = []
    for location in locations:
        if location.parent_id == parent_id:
            children = build_location_tree(locations, location.id)
            node = {
                "id": str(location.id),
                "name": location.name,
                "code": location.code,
                "locationType": location.location_type,
                "parentId": str(location.parent_id) if location.parent_id else None,
                "description": location.description,
                "address": location.address,
                "barcode": location.barcode,
                "capacity": location.capacity,
                "sortOrder": location.sort_order,
                "isActive": location.is_active,
                "createdAt": (
                    location.created_at.isoformat() if location.created_at else None
                ),
                "updatedAt": (
                    location.updated_at.isoformat() if location.updated_at else None
                ),
                "fullPath": location.full_path,
                "children": children,
            }
            tree.append(node)
    # Sort by sort_order
    tree.sort(key=lambda x: x.get("sortOrder", 0))
    return tree


def get_full_path(location: LocationModel, db: Session) -> str:
    """Get the full hierarchical path of a location."""
    parts = [location.code]
    current_id = location.parent_id
    while current_id:
        parent = db.query(LocationModel).filter(LocationModel.id == current_id).first()
        if parent:
            parts.insert(0, parent.code)
            current_id = parent.parent_id
        else:
            break
    return " > ".join(parts)


@router.get("/types", response_model=DataResponse[List[LocationTypeInfo]])
def get_location_types(request: Request):
    """
    Get all available location types with their hierarchy info.
    """
    types = []
    for loc_type in LocationType.ALL:
        types.append(
            LocationTypeInfo(
                type=loc_type,
                display_name=LocationType.DISPLAY_NAMES.get(loc_type, loc_type.title()),
                allowed_child_type=LocationType.HIERARCHY.get(loc_type),
            )
        )
    return DataResponse(data=types, meta=get_response_meta(request))


@router.get("/tree", response_model=DataResponse[List[dict]])
def get_location_tree(
    request: Request,
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve locations as a hierarchical tree structure.
    """
    query = db.query(LocationModel)

    if is_active is not None:
        query = query.filter(LocationModel.is_active == is_active)

    locations = query.order_by(LocationModel.sort_order).all()
    tree = build_location_tree(locations, None)

    return DataResponse(data=tree, meta=get_response_meta(request))


@router.get("", response_model=ListResponse[Location])
def get_locations(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
    ),
    location_type: str = Query(
        None, alias="locationType", description="Filter by location type"
    ),
    parent_id: str = Query(
        None, alias="parentId", description="Filter by parent location ID"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve locations with pagination.
    """
    query = db.query(LocationModel)

    # Apply filters
    if is_active is not None:
        query = query.filter(LocationModel.is_active == is_active)

    if location_type is not None:
        query = query.filter(LocationModel.location_type == location_type)

    if parent_id is not None:
        if parent_id == "null" or parent_id == "":
            query = query.filter(LocationModel.parent_id.is_(None))
        else:
            query = query.filter(LocationModel.parent_id == parent_id)

    # Order by sort_order
    query = query.order_by(LocationModel.sort_order)

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Get items
    locations = query.offset(skip).limit(page_size).all()

    return ListResponse(
        data=locations,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get("/{location_id}", response_model=DataResponse[Location])
def get_location(location_id: UUID, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific location by ID.
    """
    location = db.query(LocationModel).filter(LocationModel.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return DataResponse(data=location, meta=get_response_meta(request))


@router.get("/{location_id}/children", response_model=ListResponse[Location])
def get_location_children(
    location_id: UUID,
    request: Request,
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
    ),
    db: Session = Depends(get_db),
):
    """
    Get all direct children of a location.
    """
    # Verify parent exists
    parent = db.query(LocationModel).filter(LocationModel.id == location_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent location not found")

    query = db.query(LocationModel).filter(LocationModel.parent_id == location_id)

    if is_active is not None:
        query = query.filter(LocationModel.is_active == is_active)

    children = query.order_by(LocationModel.sort_order).all()

    return ListResponse(
        data=children,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=1,
            page_size=len(children),
            total_items=len(children),
            total_pages=1,
        ),
    )


@router.post("", response_model=DataResponse[Location], status_code=201)
def create_location(
    location: LocationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new location.
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Check if code already exists
    existing_location = (
        db.query(LocationModel).filter(LocationModel.code == location.code).first()
    )
    if existing_location:
        raise HTTPException(status_code=400, detail="Location code already exists")

    # Validate parent_id and location_type hierarchy
    if location.parent_id:
        parent = (
            db.query(LocationModel)
            .filter(LocationModel.id == location.parent_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent location not found")

        # Validate hierarchy - child type must be the allowed type for parent
        allowed_child = LocationType.HIERARCHY.get(parent.location_type)
        if allowed_child and location.location_type != allowed_child:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid location type. {parent.location_type.title()} can only contain {allowed_child.title()} locations",
            )
    else:
        # Root locations must be warehouses
        if location.location_type != LocationType.WAREHOUSE:
            raise HTTPException(
                status_code=400,
                detail="Top-level locations must be warehouses",
            )

    # Check barcode uniqueness if provided
    if location.barcode:
        existing_barcode = (
            db.query(LocationModel)
            .filter(LocationModel.barcode == location.barcode)
            .first()
        )
        if existing_barcode:
            raise HTTPException(status_code=400, detail="Barcode already exists")

    # Create location with tenant_id from context
    location_data = location.model_dump()
    db_location = LocationModel(
        **location_data,
        tenant_id=tenant.id,
    )
    db.add(db_location)
    db.commit()

    # Re-query to get the created location with fresh data
    created_location = (
        db.query(LocationModel).filter(LocationModel.id == db_location.id).first()
    )

    # Log the creation
    audit_service.log_create(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        entity_type=EntityType.LOCATION,
        entity_id=created_location.id,
        entity_name=f"{created_location.code} - {created_location.name}",
        data=location.model_dump(),
        request=request,
    )

    return DataResponse(data=created_location, meta=get_response_meta(request))


@router.put("/{location_id}", response_model=DataResponse[Location])
def update_location(
    location_id: UUID,
    location: LocationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update a location.
    """
    tenant = get_current_tenant()

    db_location = (
        db.query(LocationModel).filter(LocationModel.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Capture old values for audit
    old_values = {
        "name": db_location.name,
        "code": db_location.code,
        "description": db_location.description,
        "location_type": db_location.location_type,
        "parent_id": str(db_location.parent_id) if db_location.parent_id else None,
        "address": db_location.address,
        "barcode": db_location.barcode,
        "capacity": db_location.capacity,
        "sort_order": db_location.sort_order,
        "is_active": db_location.is_active,
    }

    update_data = location.model_dump(exclude_unset=True)

    # Check if new code conflicts with existing
    if "code" in update_data and update_data["code"] != db_location.code:
        existing = (
            db.query(LocationModel)
            .filter(LocationModel.code == update_data["code"])
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Location code already exists")

    # Check barcode uniqueness if being changed
    if "barcode" in update_data and update_data["barcode"] != db_location.barcode:
        if update_data["barcode"]:
            existing_barcode = (
                db.query(LocationModel)
                .filter(LocationModel.barcode == update_data["barcode"])
                .first()
            )
            if existing_barcode:
                raise HTTPException(status_code=400, detail="Barcode already exists")

    # Validate parent_id change
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if new_parent_id:
            # Can't set self as parent
            if str(new_parent_id) == str(location_id):
                raise HTTPException(
                    status_code=400, detail="Location cannot be its own parent"
                )

            parent = (
                db.query(LocationModel)
                .filter(LocationModel.id == new_parent_id)
                .first()
            )
            if not parent:
                raise HTTPException(status_code=400, detail="Parent location not found")

            # Validate hierarchy
            loc_type = update_data.get("location_type", db_location.location_type)
            allowed_child = LocationType.HIERARCHY.get(parent.location_type)
            if allowed_child and loc_type != allowed_child:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid location type. {parent.location_type.title()} can only contain {allowed_child.title()} locations",
                )

    for field, value in update_data.items():
        setattr(db_location, field, value)

    db.commit()

    # Re-query to get fresh data
    updated_location = (
        db.query(LocationModel).filter(LocationModel.id == location_id).first()
    )

    # Log the update with changes
    if tenant:
        changes = {}
        for field, new_value in update_data.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}

        if changes:
            audit_service.log_update(
                db=db,
                tenant_id=tenant.id,
                user_id=user.id,
                entity_type=EntityType.LOCATION,
                entity_id=updated_location.id,
                entity_name=f"{updated_location.code} - {updated_location.name}",
                changes=changes,
                request=request,
            )

    return DataResponse(data=updated_location, meta=get_response_meta(request))


@router.delete("/{location_id}", response_model=MessageResponse)
def delete_location(
    location_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a location. Will cascade delete all child locations.
    """
    tenant = get_current_tenant()

    db_location = (
        db.query(LocationModel).filter(LocationModel.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Count children that will be deleted
    child_count = (
        db.query(LocationModel).filter(LocationModel.parent_id == location_id).count()
    )

    # Capture location info for audit
    location_name = f"{db_location.code} - {db_location.name}"
    location_data = {
        "code": db_location.code,
        "name": db_location.name,
        "location_type": db_location.location_type,
        "children_deleted": child_count,
    }

    db.delete(db_location)
    db.commit()

    # Log the deletion
    if tenant:
        audit_service.log_delete(
            db=db,
            tenant_id=tenant.id,
            user_id=user.id,
            entity_type=EntityType.LOCATION,
            entity_id=location_id,
            entity_name=location_name,
            data=location_data,
            request=request,
        )

    message = "Location deleted successfully"
    if child_count > 0:
        message = f"Location and {child_count} child location(s) deleted successfully"

    return MessageResponse(message=message, meta=get_response_meta(request))
