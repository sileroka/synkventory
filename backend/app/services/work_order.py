"""
Work Order service for managing production tracking.

This service provides business logic for:
- Creating and managing work orders
- Tracking production progress
- Building assemblies through work orders
- Calculating work order statistics
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from fastapi import Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, case

from app.models.work_order import WorkOrder, WorkOrderStatus, WorkOrderPriority
from app.models.inventory import InventoryItem
from app.models.bill_of_material import BillOfMaterial
from app.models.user import User
from app.models.location import Location
from app.models.audit_log import AuditAction, EntityType
from app.services.audit import audit_service
from app.services.bom import bom_service
from app.core.tenant import get_current_tenant
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderStatusUpdate,
    WorkOrderProgressUpdate,
    WorkOrderStats,
)

logger = logging.getLogger(__name__)


class WorkOrderService:
    """Service for Work Order operations."""

    def _generate_work_order_number(self, db: Session, tenant_id: UUID) -> str:
        """
        Generate a unique work order number.
        
        Format: WO-YYYYMMDD-XXXX where XXXX is a sequence number.
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"WO-{today}-"
        
        # Find the highest sequence number for today
        last_wo = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.work_order_number.like(f"{prefix}%")
            )
            .order_by(WorkOrder.work_order_number.desc())
            .first()
        )
        
        if last_wo:
            try:
                last_seq = int(last_wo.work_order_number.split("-")[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"

    def _calculate_estimated_cost(
        self,
        db: Session,
        item_id: UUID,
        quantity: int,
    ) -> Optional[Decimal]:
        """Calculate estimated cost based on BOM component prices."""
        bom_entries = (
            db.query(BillOfMaterial)
            .filter(BillOfMaterial.parent_item_id == item_id)
            .options(joinedload(BillOfMaterial.component_item))
            .all()
        )
        
        if not bom_entries:
            return None
        
        total_cost = Decimal("0.00")
        for entry in bom_entries:
            if entry.component_item and entry.component_item.unit_price:
                component_cost = Decimal(str(entry.component_item.unit_price)) * entry.quantity_required
                total_cost += component_cost
        
        return total_cost * quantity if total_cost > 0 else None

    def get_work_orders(
        self,
        db: Session,
        status: Optional[WorkOrderStatus] = None,
        priority: Optional[WorkOrderPriority] = None,
        item_id: Optional[UUID] = None,
        assigned_to_id: Optional[UUID] = None,
        include_completed: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> Tuple[List[WorkOrder], int]:
        """
        Get paginated list of work orders with optional filters.
        
        Returns:
            Tuple of (work_orders, total_count)
        """
        query = (
            db.query(WorkOrder)
            .options(
                joinedload(WorkOrder.item),
                joinedload(WorkOrder.assigned_to),
                joinedload(WorkOrder.output_location),
            )
        )
        
        # Apply filters
        if status:
            query = query.filter(WorkOrder.status == status)
        elif not include_completed:
            query = query.filter(
                WorkOrder.status.notin_([
                    WorkOrderStatus.COMPLETED.value,
                    WorkOrderStatus.CANCELLED.value,
                ])
            )
        
        if priority:
            query = query.filter(WorkOrder.priority == priority)
        
        if item_id:
            query = query.filter(WorkOrder.item_id == item_id)
        
        if assigned_to_id:
            query = query.filter(WorkOrder.assigned_to_id == assigned_to_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        work_orders = (
            query
            .order_by(
                # Priority ordering: urgent first
                case(
                    (WorkOrder.priority == WorkOrderPriority.URGENT.value, 0),
                    (WorkOrder.priority == WorkOrderPriority.HIGH.value, 1),
                    (WorkOrder.priority == WorkOrderPriority.NORMAL.value, 2),
                    (WorkOrder.priority == WorkOrderPriority.LOW.value, 3),
                ),
                WorkOrder.due_date.asc().nulls_last(),
                WorkOrder.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        return work_orders, total

    def get_work_order(
        self,
        db: Session,
        work_order_id: UUID,
    ) -> Optional[WorkOrder]:
        """Get a single work order by ID."""
        return (
            db.query(WorkOrder)
            .filter(WorkOrder.id == work_order_id)
            .options(
                joinedload(WorkOrder.item),
                joinedload(WorkOrder.assigned_to),
                joinedload(WorkOrder.output_location),
                joinedload(WorkOrder.created_by_user),
            )
            .first()
        )

    def get_work_order_by_number(
        self,
        db: Session,
        work_order_number: str,
    ) -> Optional[WorkOrder]:
        """Get a work order by its number."""
        return (
            db.query(WorkOrder)
            .filter(WorkOrder.work_order_number == work_order_number)
            .options(
                joinedload(WorkOrder.item),
                joinedload(WorkOrder.assigned_to),
                joinedload(WorkOrder.output_location),
            )
            .first()
        )

    def create_work_order(
        self,
        db: Session,
        data: WorkOrderCreate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> WorkOrder:
        """
        Create a new work order.
        
        Args:
            db: Database session
            data: Work order creation data
            user_id: ID of the user creating the work order
            request: Optional request object for audit logging
            
        Returns:
            Created WorkOrder
            
        Raises:
            ValueError: If item has no BOM
        """
        tenant = get_current_tenant()
        
        # Verify the item exists and has a BOM
        item = db.query(InventoryItem).filter(InventoryItem.id == data.itemId).first()
        if not item:
            raise ValueError(f"Item not found: {data.itemId}")
        
        # Check if item has a BOM
        bom_count = (
            db.query(BillOfMaterial)
            .filter(BillOfMaterial.parent_item_id == data.itemId)
            .count()
        )
        if bom_count == 0:
            raise ValueError(f"Item '{item.name}' has no Bill of Materials defined")
        
        # Validate output location if provided
        if data.outputLocationId:
            location = db.query(Location).filter(Location.id == data.outputLocationId).first()
            if not location:
                raise ValueError(f"Output location not found: {data.outputLocationId}")
        
        # Validate assigned user if provided
        if data.assignedToId:
            user = db.query(User).filter(User.id == data.assignedToId).first()
            if not user:
                raise ValueError(f"Assigned user not found: {data.assignedToId}")
        
        # Generate work order number
        wo_number = self._generate_work_order_number(db, tenant.id)
        
        # Calculate estimated cost
        estimated_cost = self._calculate_estimated_cost(db, data.itemId, data.quantityOrdered)
        
        # Create work order
        work_order = WorkOrder(
            tenant_id=tenant.id,
            work_order_number=wo_number,
            item_id=data.itemId,
            quantity_ordered=data.quantityOrdered,
            quantity_completed=0,
            quantity_scrapped=0,
            status=WorkOrderStatus.DRAFT,
            priority=data.priority,
            due_date=data.dueDate,
            output_location_id=data.outputLocationId,
            assigned_to_id=data.assignedToId,
            description=data.description,
            notes=data.notes,
            estimated_cost=estimated_cost,
            created_by=user_id,
            updated_by=user_id,
        )
        
        db.add(work_order)
        db.flush()
        
        # Audit log
        audit_service.log(
            db=db,
            action=AuditAction.CREATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order.id,
            user_id=user_id,
            changes={
                "work_order_number": wo_number,
                "item_id": str(data.itemId),
                "quantity_ordered": data.quantityOrdered,
                "priority": data.priority.value,
            },
            request=request,
        )
        
        db.commit()
        db.refresh(work_order)
        
        logger.info(f"Created work order {wo_number} for item {item.name}")
        return work_order

    def update_work_order(
        self,
        db: Session,
        work_order_id: UUID,
        data: WorkOrderUpdate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> WorkOrder:
        """Update a work order."""
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            raise ValueError(f"Work order not found: {work_order_id}")
        
        # Can't update completed or cancelled orders
        if work_order.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]:
            raise ValueError(f"Cannot update {work_order.status.value} work order")
        
        changes = {}
        
        if data.quantityOrdered is not None and data.quantityOrdered != work_order.quantity_ordered:
            # Recalculate estimated cost if quantity changes
            work_order.estimated_cost = self._calculate_estimated_cost(
                db, work_order.item_id, data.quantityOrdered
            )
            changes["quantity_ordered"] = {
                "old": work_order.quantity_ordered,
                "new": data.quantityOrdered,
            }
            work_order.quantity_ordered = data.quantityOrdered
        
        if data.priority is not None and data.priority != work_order.priority:
            changes["priority"] = {
                "old": work_order.priority.value,
                "new": data.priority.value,
            }
            work_order.priority = data.priority
        
        if data.dueDate is not None:
            changes["due_date"] = {
                "old": str(work_order.due_date) if work_order.due_date else None,
                "new": str(data.dueDate),
            }
            work_order.due_date = data.dueDate
        
        if data.outputLocationId is not None:
            if data.outputLocationId:
                location = db.query(Location).filter(Location.id == data.outputLocationId).first()
                if not location:
                    raise ValueError(f"Output location not found: {data.outputLocationId}")
            work_order.output_location_id = data.outputLocationId
        
        if data.assignedToId is not None:
            if data.assignedToId:
                user = db.query(User).filter(User.id == data.assignedToId).first()
                if not user:
                    raise ValueError(f"Assigned user not found: {data.assignedToId}")
            changes["assigned_to_id"] = {
                "old": str(work_order.assigned_to_id) if work_order.assigned_to_id else None,
                "new": str(data.assignedToId) if data.assignedToId else None,
            }
            work_order.assigned_to_id = data.assignedToId
        
        if data.description is not None:
            work_order.description = data.description
        
        if data.notes is not None:
            work_order.notes = data.notes
        
        work_order.updated_by = user_id
        work_order.updated_at = datetime.utcnow()
        
        if changes:
            audit_service.log(
                db=db,
                action=AuditAction.UPDATE,
                entity_type=EntityType.WORK_ORDER,
                entity_id=work_order_id,
                user_id=user_id,
                changes=changes,
                request=request,
            )
        
        db.commit()
        db.refresh(work_order)
        
        return work_order

    def update_status(
        self,
        db: Session,
        work_order_id: UUID,
        data: WorkOrderStatusUpdate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> WorkOrder:
        """Update work order status."""
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            raise ValueError(f"Work order not found: {work_order_id}")
        
        old_status = work_order.status
        new_status = data.status
        
        # Validate status transitions
        valid_transitions = {
            WorkOrderStatus.DRAFT: [WorkOrderStatus.PENDING, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.PENDING: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.ON_HOLD, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.IN_PROGRESS: [WorkOrderStatus.ON_HOLD, WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.ON_HOLD: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.COMPLETED: [],  # No transitions from completed
            WorkOrderStatus.CANCELLED: [],  # No transitions from cancelled
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(
                f"Invalid status transition from {old_status.value} to {new_status.value}"
            )
        
        work_order.status = new_status
        work_order.updated_by = user_id
        work_order.updated_at = datetime.utcnow()
        
        # Update timestamps based on status
        if new_status == WorkOrderStatus.IN_PROGRESS and not work_order.start_date:
            work_order.start_date = datetime.utcnow()
        elif new_status == WorkOrderStatus.COMPLETED:
            work_order.completed_date = datetime.utcnow()
        
        if data.notes:
            # Append to existing notes
            if work_order.notes:
                work_order.notes = f"{work_order.notes}\n\n[{datetime.utcnow().isoformat()}] Status changed to {new_status.value}: {data.notes}"
            else:
                work_order.notes = f"[{datetime.utcnow().isoformat()}] Status changed to {new_status.value}: {data.notes}"
        
        audit_service.log(
            db=db,
            action=AuditAction.UPDATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order_id,
            user_id=user_id,
            changes={
                "status": {"old": old_status.value, "new": new_status.value},
                "notes": data.notes,
            },
            request=request,
        )
        
        db.commit()
        db.refresh(work_order)
        
        logger.info(f"Work order {work_order.work_order_number} status changed: {old_status.value} -> {new_status.value}")
        return work_order

    def record_progress(
        self,
        db: Session,
        work_order_id: UUID,
        data: WorkOrderProgressUpdate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> WorkOrder:
        """
        Record production progress for a work order.
        
        This updates the completed/scrapped quantities without actually
        building the items. Use build_from_work_order to actually consume
        components and produce the assembly.
        """
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            raise ValueError(f"Work order not found: {work_order_id}")
        
        if work_order.status not in [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.PENDING]:
            raise ValueError(f"Cannot record progress for {work_order.status.value} work order")
        
        # Validate quantities
        total_after = data.quantityCompleted + (data.quantityScrapped or 0)
        if total_after > work_order.quantity_ordered:
            raise ValueError(
                f"Total completed ({data.quantityCompleted}) + scrapped ({data.quantityScrapped}) "
                f"cannot exceed ordered quantity ({work_order.quantity_ordered})"
            )
        
        old_completed = work_order.quantity_completed
        old_scrapped = work_order.quantity_scrapped
        
        work_order.quantity_completed = data.quantityCompleted
        work_order.quantity_scrapped = data.quantityScrapped or 0
        work_order.updated_by = user_id
        work_order.updated_at = datetime.utcnow()
        
        # Auto-start if recording first progress
        if work_order.status == WorkOrderStatus.PENDING and data.quantityCompleted > 0:
            work_order.status = WorkOrderStatus.IN_PROGRESS
            work_order.start_date = datetime.utcnow()
        
        # Auto-complete if all ordered
        remaining = work_order.quantity_ordered - work_order.quantity_completed - work_order.quantity_scrapped
        if remaining <= 0:
            work_order.status = WorkOrderStatus.COMPLETED
            work_order.completed_date = datetime.utcnow()
        
        if data.notes:
            timestamp = datetime.utcnow().isoformat()
            progress_note = f"[{timestamp}] Progress: {data.quantityCompleted} completed, {data.quantityScrapped or 0} scrapped"
            if data.notes:
                progress_note += f" - {data.notes}"
            
            if work_order.notes:
                work_order.notes = f"{work_order.notes}\n\n{progress_note}"
            else:
                work_order.notes = progress_note
        
        audit_service.log(
            db=db,
            action=AuditAction.UPDATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order_id,
            user_id=user_id,
            changes={
                "quantity_completed": {"old": old_completed, "new": data.quantityCompleted},
                "quantity_scrapped": {"old": old_scrapped, "new": data.quantityScrapped or 0},
            },
            request=request,
        )
        
        db.commit()
        db.refresh(work_order)
        
        return work_order

    def build_from_work_order(
        self,
        db: Session,
        work_order_id: UUID,
        quantity: int,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> WorkOrder:
        """
        Build assemblies for a work order using the BOM service.
        
        This consumes components and produces the assembly items,
        then updates the work order progress.
        """
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            raise ValueError(f"Work order not found: {work_order_id}")
        
        if work_order.status not in [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.PENDING]:
            raise ValueError(f"Cannot build for {work_order.status.value} work order")
        
        remaining = work_order.quantity_ordered - work_order.quantity_completed - work_order.quantity_scrapped
        if quantity > remaining:
            raise ValueError(f"Cannot build {quantity} units. Only {remaining} remaining on this work order.")
        
        # Use BOM service to perform the build
        build_result = bom_service.build_assembly(
            db=db,
            parent_item_id=work_order.item_id,
            quantity=quantity,
            user_id=user_id,
            location_id=work_order.output_location_id,
            notes=f"Built via Work Order {work_order.work_order_number}",
            request=request,
        )
        
        # Update work order progress
        work_order.quantity_completed += quantity
        work_order.updated_by = user_id
        work_order.updated_at = datetime.utcnow()
        
        # Calculate actual cost from build
        if build_result.get("total_cost"):
            if work_order.actual_cost:
                work_order.actual_cost += Decimal(str(build_result["total_cost"]))
            else:
                work_order.actual_cost = Decimal(str(build_result["total_cost"]))
        
        # Auto-start if this is first build
        if work_order.status == WorkOrderStatus.PENDING:
            work_order.status = WorkOrderStatus.IN_PROGRESS
            work_order.start_date = datetime.utcnow()
        
        # Check if complete
        new_remaining = work_order.quantity_ordered - work_order.quantity_completed - work_order.quantity_scrapped
        if new_remaining <= 0:
            work_order.status = WorkOrderStatus.COMPLETED
            work_order.completed_date = datetime.utcnow()
        
        # Add build note
        timestamp = datetime.utcnow().isoformat()
        build_note = f"[{timestamp}] Built {quantity} units via BOM"
        if work_order.notes:
            work_order.notes = f"{work_order.notes}\n\n{build_note}"
        else:
            work_order.notes = build_note
        
        audit_service.log(
            db=db,
            action=AuditAction.UPDATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order_id,
            user_id=user_id,
            changes={
                "build_quantity": quantity,
                "quantity_completed": work_order.quantity_completed,
            },
            request=request,
        )
        
        db.commit()
        db.refresh(work_order)
        
        return work_order

    def delete_work_order(
        self,
        db: Session,
        work_order_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> bool:
        """
        Delete a work order (only if draft or cancelled).
        """
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            raise ValueError(f"Work order not found: {work_order_id}")
        
        if work_order.status not in [WorkOrderStatus.DRAFT, WorkOrderStatus.CANCELLED]:
            raise ValueError(
                f"Cannot delete {work_order.status.value} work order. "
                "Only draft or cancelled work orders can be deleted."
            )
        
        wo_number = work_order.work_order_number
        
        audit_service.log(
            db=db,
            action=AuditAction.DELETE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order_id,
            user_id=user_id,
            changes={"work_order_number": wo_number},
            request=request,
        )
        
        db.delete(work_order)
        db.commit()
        
        logger.info(f"Deleted work order {wo_number}")
        return True

    def get_stats(self, db: Session) -> WorkOrderStats:
        """Get work order statistics."""
        stats = WorkOrderStats()
        
        # Count by status
        status_counts = (
            db.query(WorkOrder.status, func.count(WorkOrder.id))
            .group_by(WorkOrder.status)
            .all()
        )
        
        for status, count in status_counts:
            stats.total += count
            if status == WorkOrderStatus.DRAFT:
                stats.draft = count
            elif status == WorkOrderStatus.PENDING:
                stats.pending = count
            elif status == WorkOrderStatus.IN_PROGRESS:
                stats.inProgress = count
            elif status == WorkOrderStatus.ON_HOLD:
                stats.onHold = count
            elif status == WorkOrderStatus.COMPLETED:
                stats.completed = count
            elif status == WorkOrderStatus.CANCELLED:
                stats.cancelled = count
        
        # Count overdue
        now = datetime.utcnow()
        stats.overdue = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.due_date < now,
                WorkOrder.status.notin_([
                    WorkOrderStatus.COMPLETED.value,
                    WorkOrderStatus.CANCELLED.value,
                ]),
            )
            .count()
        )
        
        return stats

    def get_work_orders_for_item(
        self,
        db: Session,
        item_id: UUID,
        include_completed: bool = False,
    ) -> List[WorkOrder]:
        """Get all work orders for a specific item."""
        query = (
            db.query(WorkOrder)
            .filter(WorkOrder.item_id == item_id)
            .options(joinedload(WorkOrder.assigned_to))
        )
        
        if not include_completed:
            query = query.filter(
                WorkOrder.status.notin_([
                    WorkOrderStatus.COMPLETED.value,
                    WorkOrderStatus.CANCELLED.value,
                ])
            )
        
        return (
            query
            .order_by(WorkOrder.created_at.desc())
            .all()
        )


# Singleton instance
work_order_service = WorkOrderService()
