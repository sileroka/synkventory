"""
Audit logs API endpoints.
"""

import math
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog as AuditLogModel
from app.schemas.audit_log import AuditLog, AuditLogSummary
from app.schemas.response import ListResponse, PaginationMeta, ResponseMeta

# Only authenticated users can view audit logs
router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("", response_model=ListResponse[AuditLog])
def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        50, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    user_id: Optional[UUID] = Query(
        None, alias="userId", description="Filter by user ID"
    ),
    action: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(
        None, alias="entityType", description="Filter by entity type"
    ),
    entity_id: Optional[UUID] = Query(
        None, alias="entityId", description="Filter by entity ID"
    ),
    start_date: Optional[date] = Query(
        None, alias="startDate", description="Filter from this date"
    ),
    end_date: Optional[date] = Query(
        None, alias="endDate", description="Filter until this date"
    ),
    search: Optional[str] = Query(
        None, description="Search in entity name or user email"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve audit logs with pagination and filtering.

    Filters:
    - userId: Filter by specific user
    - action: Filter by action type (LOGIN, CREATE, UPDATE, DELETE, etc.)
    - entityType: Filter by entity type (USER, INVENTORY_ITEM, etc.)
    - entityId: Filter by specific entity
    - startDate/endDate: Filter by date range
    - search: Search in entity name or user email
    """
    query = db.query(AuditLogModel)

    # Apply filters
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    if action:
        query = query.filter(AuditLogModel.action == action)
    if entity_type:
        query = query.filter(AuditLogModel.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLogModel.entity_id == entity_id)
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
            (AuditLogModel.entity_name.ilike(search_term))
            | (AuditLogModel.user_email.ilike(search_term))
        )

    # Get total count
    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Apply pagination and ordering (newest first)
    skip = (page - 1) * page_size
    logs = (
        query.order_by(desc(AuditLogModel.created_at))
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return ListResponse(
        data=logs,
        meta=PaginationMeta(
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get("/actions", response_model=List[str])
def get_audit_actions(db: Session = Depends(get_db)):
    """Get list of distinct action types in the audit log."""
    results = db.query(AuditLogModel.action).distinct().all()
    return [r[0] for r in results if r[0]]


@router.get("/entity-types", response_model=List[str])
def get_entity_types(db: Session = Depends(get_db)):
    """Get list of distinct entity types in the audit log."""
    results = db.query(AuditLogModel.entity_type).distinct().all()
    return [r[0] for r in results if r[0]]


@router.get("/summary", response_model=AuditLogSummary)
def get_audit_summary(
    request: Request,
    start_date: Optional[date] = Query(
        None, alias="startDate", description="Summary from this date"
    ),
    end_date: Optional[date] = Query(
        None, alias="endDate", description="Summary until this date"
    ),
    db: Session = Depends(get_db),
):
    """
    Get summary statistics of audit logs.

    Returns counts of logs by action type and entity type.
    """
    query = db.query(AuditLogModel)

    if start_date:
        query = query.filter(
            AuditLogModel.created_at
            >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query = query.filter(
            AuditLogModel.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_count = query.count()

    # Count by action
    action_counts = {}
    action_results = (
        db.query(AuditLogModel.action, db.func.count(AuditLogModel.id))
        .group_by(AuditLogModel.action)
        .all()
    )
    for action, count in action_results:
        if action:
            action_counts[action] = count

    # Count by entity type
    entity_counts = {}
    entity_results = (
        db.query(AuditLogModel.entity_type, db.func.count(AuditLogModel.id))
        .group_by(AuditLogModel.entity_type)
        .all()
    )
    for entity_type, count in entity_results:
        if entity_type:
            entity_counts[entity_type] = count

    return AuditLogSummary(
        total_count=total_count,
        action_counts=action_counts,
        entity_counts=entity_counts,
    )


@router.get("/{log_id}", response_model=AuditLog)
def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific audit log entry by ID."""
    from fastapi import HTTPException

    log = db.query(AuditLogModel).filter(AuditLogModel.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log
