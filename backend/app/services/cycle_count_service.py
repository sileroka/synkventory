"""
Service functions for Cycle Counts: scheduling, recording, status transitions,
and applying inventory adjustments.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.cycle_count import CycleCount, CycleCountLineItem, CycleCountStatus
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.inventory_location_quantity import (
    InventoryLocationQuantity as InventoryLocationQuantityModel,
)
from app.schemas.stock_movement import StockMovementCreate, MovementType as MovementTypeSchema
from app.services.stock_movement_service import stock_movement_service
from app.services.audit import audit_service
from app.models.audit_log import AuditAction, EntityType


def _get_expected_quantity(
    db: Session, item_id: UUID | str, location_id: Optional[UUID | str]
) -> int:
    """Resolve expected quantity either for a specific location or overall item."""
    if location_id:
        loc_qty = (
            db.query(InventoryLocationQuantityModel)
            .filter(
                InventoryLocationQuantityModel.inventory_item_id == item_id,
                InventoryLocationQuantityModel.location_id == location_id,
            )
            .first()
        )
        return int(loc_qty.quantity) if loc_qty else 0
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        return 0
    # Use total quantity (across locations) if available
    try:
        return int(item.total_quantity)
    except Exception:
        return int(item.quantity or 0)


def create_cycle_count(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    scheduled_date: date,
    description: Optional[str],
    line_items: List[Dict[str, Any]],
) -> CycleCount:
    """Create a cycle count in Scheduled status and prefill expected quantities."""
    cc = CycleCount(
        tenant_id=tenant_id,
        scheduled_date=scheduled_date,
        status=CycleCountStatus.SCHEDULED,
        description=description,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(cc)
    db.flush()

    created_count = 0
    for li in line_items or []:
        item_id = li.get("item_id")
        if not item_id:
            raise HTTPException(status_code=400, detail="Line item missing item_id")
        location_id = li.get("location_id")
        expected = _get_expected_quantity(db, item_id, location_id)
        db_li = CycleCountLineItem(
            tenant_id=tenant_id,
            cycle_count_id=cc.id,
            item_id=item_id,
            location_id=location_id,
            expected_quantity=expected,
            counted_quantity=0,
            notes=li.get("notes"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(db_li)
        created_count += 1

    db.commit()
    db.refresh(cc)

    audit_service.log_create(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=getattr(EntityType, "CYCLE_COUNT", "CYCLE_COUNT"),
        entity_id=cc.id,
        entity_name=f"CycleCount {cc.id}",
        data={
            "scheduled_date": str(scheduled_date),
            "description": description,
            "line_items": created_count,
        },
    )

    return cc


def get_cycle_counts(
    db: Session,
    tenant_id: UUID,
    status: Optional[CycleCountStatus] = None,
    date_range: Optional[Tuple[date, date]] = None,
    page: int = 1,
    page_size: int = 25,
) -> List[CycleCount]:
    """List cycle counts filtered by status/date range with pagination."""
    q = db.query(CycleCount).filter(CycleCount.tenant_id == tenant_id)
    if status:
        q = q.filter(CycleCount.status == status)
    if date_range:
        start, end = date_range
        q = q.filter(CycleCount.scheduled_date.between(start, end))

    q = q.order_by(CycleCount.scheduled_date.desc())
    offset = max(0, (page - 1) * page_size)
    items = q.offset(offset).limit(page_size).all()
    return items


def get_cycle_count(db: Session, tenant_id: UUID, count_id: UUID) -> Optional[CycleCount]:
    """Retrieve a single cycle count with line items."""
    cc = (
        db.query(CycleCount)
        .options(joinedload(CycleCount.line_items))
        .filter(CycleCount.tenant_id == tenant_id, CycleCount.id == count_id)
        .first()
    )
    return cc


def update_cycle_count(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    count_id: UUID,
    **fields: Any,
) -> CycleCount:
    """Update description or reschedule a cycle count."""
    cc = (
        db.query(CycleCount)
        .filter(CycleCount.tenant_id == tenant_id, CycleCount.id == count_id)
        .first()
    )
    if not cc:
        raise HTTPException(status_code=404, detail="Cycle count not found")

    changes: Dict[str, Dict[str, Any]] = {}
    if "scheduled_date" in fields and fields["scheduled_date"] is not None:
        old = cc.scheduled_date
        cc.scheduled_date = fields["scheduled_date"]
        changes["scheduled_date"] = {"old": str(old), "new": str(cc.scheduled_date)}
    if "description" in fields and fields["description"] is not None:
        old = cc.description
        cc.description = fields["description"]
        changes["description"] = {"old": old, "new": cc.description}

    cc.updated_by = user_id
    cc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cc)

    audit_service.log_update(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=getattr(EntityType, "CYCLE_COUNT", "CYCLE_COUNT"),
        entity_id=cc.id,
        entity_name=f"CycleCount {cc.id}",
        changes=changes,
    )

    return cc


def _can_transition(current: CycleCountStatus, new: CycleCountStatus) -> bool:
    allowed = {
        CycleCountStatus.SCHEDULED: {CycleCountStatus.IN_PROGRESS, CycleCountStatus.CANCELLED},
        CycleCountStatus.IN_PROGRESS: {CycleCountStatus.COMPLETED, CycleCountStatus.CANCELLED},
        CycleCountStatus.COMPLETED: {CycleCountStatus.APPROVED},
        CycleCountStatus.APPROVED: set(),
        CycleCountStatus.CANCELLED: set(),
    }
    return new in allowed.get(current, set())


def update_status(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    count_id: UUID,
    new_status: CycleCountStatus,
) -> CycleCount:
    """Update cycle count status enforcing workflow transitions."""
    cc = (
        db.query(CycleCount)
        .filter(CycleCount.tenant_id == tenant_id, CycleCount.id == count_id)
        .first()
    )
    if not cc:
        raise HTTPException(status_code=404, detail="Cycle count not found")

    if not _can_transition(cc.status, new_status):
        raise HTTPException(status_code=400, detail=f"Invalid transition: {cc.status.value} -> {new_status.value}")

    old_status = cc.status
    cc.status = new_status
    cc.updated_by = user_id
    cc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cc)

    audit_service.log_update(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=getattr(EntityType, "CYCLE_COUNT", "CYCLE_COUNT"),
        entity_id=cc.id,
        entity_name=f"CycleCount {cc.id}",
        changes={"status": {"old": old_status.value, "new": new_status.value}},
    )

    return cc


def record_counts(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    count_id: UUID,
    line_item_updates: List[Dict[str, Any]],
) -> CycleCount:
    """Record counted quantities and optional notes for line items."""
    cc = (
        db.query(CycleCount)
        .options(joinedload(CycleCount.line_items))
        .filter(CycleCount.tenant_id == tenant_id, CycleCount.id == count_id)
        .first()
    )
    if not cc:
        raise HTTPException(status_code=404, detail="Cycle count not found")

    # Allow recording counts in IN_PROGRESS or COMPLETED states
    if cc.status not in {CycleCountStatus.IN_PROGRESS, CycleCountStatus.COMPLETED}:
        raise HTTPException(status_code=400, detail="Counts can only be recorded when InProgress or Completed")

    updated = 0
    for upd in line_item_updates or []:
        li_id = upd.get("id")
        counted = upd.get("counted_quantity")
        notes = upd.get("notes")
        if not li_id:
            raise HTTPException(status_code=400, detail="Line item update missing id")
        li = next((x for x in cc.line_items if str(x.id) == str(li_id)), None)
        if not li:
            raise HTTPException(status_code=404, detail=f"Line item {li_id} not found")
        if counted is not None:
            li.counted_quantity = int(counted)
        if notes is not None:
            li.notes = notes
        li.updated_by = user_id
        li.updated_at = datetime.utcnow()
        updated += 1

    cc.updated_by = user_id
    cc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cc)

    audit_service.log_bulk_operation(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action=AuditAction.UPDATE,
        entity_type=getattr(EntityType, "CYCLE_COUNT", "CYCLE_COUNT"),
        count=updated,
        data={"cycle_count_id": str(cc.id)},
    )

    return cc


def apply_adjustments(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    count_id: UUID,
) -> CycleCount:
    """Apply inventory adjustments for variances on an Approved cycle count."""
    cc = (
        db.query(CycleCount)
        .options(joinedload(CycleCount.line_items))
        .filter(CycleCount.tenant_id == tenant_id, CycleCount.id == count_id)
        .first()
    )
    if not cc:
        raise HTTPException(status_code=404, detail="Cycle count not found")

    if cc.status != CycleCountStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Adjustments can only be applied when count is Approved")

    applied = 0
    for li in cc.line_items:
        variance = int(li.counted_quantity or 0) - int(li.expected_quantity or 0)
        if variance == 0:
            continue

        # Determine movement direction and location context
        movement = StockMovementCreate(
            inventory_item_id=str(li.item_id),
            movement_type=MovementTypeSchema.ADJUST,
            quantity=variance,
            reference_number=f"cycle:{cc.id}",
            notes=f"Cycle count variance: {variance}",
        )

        # Location routing: positive -> to_location_id, negative -> from_location_id
        location_id = str(li.location_id) if li.location_id else None
        if variance > 0:
            # If no location specified, try item's default location
            if not location_id:
                item = (
                    db.query(InventoryItemModel)
                    .filter(InventoryItemModel.id == li.item_id)
                    .first()
                )
                location_id = str(item.location_id) if item and item.location_id else None
            if not location_id:
                raise HTTPException(status_code=400, detail="Positive adjustment requires a destination location")
            movement.to_location_id = location_id
        else:
            if not location_id:
                item = (
                    db.query(InventoryItemModel)
                    .filter(InventoryItemModel.id == li.item_id)
                    .first()
                )
                location_id = str(item.location_id) if item and item.location_id else None
            if not location_id:
                raise HTTPException(status_code=400, detail="Negative adjustment requires a source location")
            movement.from_location_id = location_id

        stock_movement_service.create_movement(
            db=db,
            movement=movement,
            user_id=user_id,
            request=None,
        )
        applied += 1

    # No status change here; adjustments are executed under Approved state
    db.commit()
    db.refresh(cc)

    audit_service.log_bulk_operation(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action=AuditAction.STOCK_ADJUST,
        entity_type=getattr(EntityType, "CYCLE_COUNT", "CYCLE_COUNT"),
        count=applied,
        data={"cycle_count_id": str(cc.id)},
    )

    return cc
