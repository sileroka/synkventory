import math
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.location import Location as LocationModel
from app.schemas.location import (
    Location,
    LocationCreate,
    LocationUpdate,
)
from app.schemas.response import (
    DataResponse,
    ListResponse,
    PaginationMeta,
    ResponseMeta,
    MessageResponse,
)

router = APIRouter()


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/", response_model=ListResponse[Location])
def get_locations(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        25, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    is_active: bool = Query(
        None, alias="isActive", description="Filter by active status"
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


@router.post("/", response_model=DataResponse[Location], status_code=201)
def create_location(
    location: LocationCreate, request: Request, db: Session = Depends(get_db)
):
    """
    Create a new location.
    """
    # Check if code already exists
    existing_location = (
        db.query(LocationModel).filter(LocationModel.code == location.code).first()
    )
    if existing_location:
        raise HTTPException(status_code=400, detail="Location code already exists")

    db_location = LocationModel(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return DataResponse(data=db_location, meta=get_response_meta(request))


@router.put("/{location_id}", response_model=DataResponse[Location])
def update_location(
    location_id: UUID,
    location: LocationUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update a location.
    """
    db_location = (
        db.query(LocationModel).filter(LocationModel.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

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

    for field, value in update_data.items():
        setattr(db_location, field, value)

    db.commit()
    db.refresh(db_location)
    return DataResponse(data=db_location, meta=get_response_meta(request))


@router.delete("/{location_id}", response_model=MessageResponse)
def delete_location(location_id: UUID, request: Request, db: Session = Depends(get_db)):
    """
    Delete a location.
    """
    db_location = (
        db.query(LocationModel).filter(LocationModel.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(db_location)
    db.commit()
    return MessageResponse(
        message="Location deleted successfully", meta=get_response_meta(request)
    )
