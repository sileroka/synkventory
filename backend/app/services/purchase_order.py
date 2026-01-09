"""
Service layer for Purchase Order operations.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, case, or_
from sqlalchemy.orm import Session, joinedload

from app.core.tenant import get_current_tenant
from app.models.audit_log import EntityType
from app.models.inventory import InventoryItem
from app.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderLineItem,
    PurchaseOrderStatus,
    PurchaseOrderPriority,
)
from app.models.stock_movement import StockMovement, MovementType
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderStats,
    LowStockItem,
    LowStockSuggestion,
    ReceiveItemsRequest,
)
from app.services.audit import audit_service
from app.services.lot import lot_service

logger = logging.getLogger(__name__)


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    PurchaseOrderStatus.DRAFT: [
        PurchaseOrderStatus.PENDING_APPROVAL,
        PurchaseOrderStatus.APPROVED,  # Skip approval for admins
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.PENDING_APPROVAL: [
        PurchaseOrderStatus.APPROVED,
        PurchaseOrderStatus.DRAFT,  # Return for revision
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.APPROVED: [
        PurchaseOrderStatus.ORDERED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.ORDERED: [
        PurchaseOrderStatus.PARTIALLY_RECEIVED,
        PurchaseOrderStatus.RECEIVED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.PARTIALLY_RECEIVED: [
        PurchaseOrderStatus.RECEIVED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.RECEIVED: [],  # Terminal state
    PurchaseOrderStatus.CANCELLED: [],  # Terminal state
}


class PurchaseOrderService:
    """Service for managing purchase orders."""

    def generate_po_number(self, db: Session) -> str:
        """Generate a unique PO number."""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"PO-{today}-"

        # Find the highest number for today
        latest = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number.like(f"{prefix}%"))
            .order_by(PurchaseOrder.po_number.desc())
            .first()
        )

        if latest:
            try:
                last_num = int(latest.po_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def get_purchase_orders(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 25,
        status: Optional[PurchaseOrderStatus] = None,
        priority: Optional[PurchaseOrderPriority] = None,
        include_received: bool = False,
        supplier_name: Optional[str] = None,
        supplier_id: Optional[UUID] = None,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get paginated list of purchase orders."""
        query = db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.requested_by),
            joinedload(PurchaseOrder.receiving_location),
            joinedload(PurchaseOrder.supplier),
        )

        # Apply filters
        if status:
            query = query.filter(PurchaseOrder.status == status)
        elif not include_received:
            query = query.filter(
                PurchaseOrder.status.notin_(
                    [
                        PurchaseOrderStatus.RECEIVED.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    ]
                )
            )

        if priority:
            query = query.filter(PurchaseOrder.priority == priority)

        if supplier_name:
            # Match either text-only supplier_name on PO or linked Supplier.name
            query = (
                query.outerjoin(Supplier, PurchaseOrder.supplier_id == Supplier.id)
                .filter(
                    or_(
                        PurchaseOrder.supplier_name.ilike(f"%{supplier_name}%"),
                        Supplier.name.ilike(f"%{supplier_name}%"),
                    )
                )
            )

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        purchase_orders = (
            query.order_by(
                # Priority ordering
                case(
                    (PurchaseOrder.priority == PurchaseOrderPriority.URGENT.value, 0),
                    (PurchaseOrder.priority == PurchaseOrderPriority.HIGH.value, 1),
                    (PurchaseOrder.priority == PurchaseOrderPriority.NORMAL.value, 2),
                    (PurchaseOrder.priority == PurchaseOrderPriority.LOW.value, 3),
                ),
                PurchaseOrder.expected_date.asc().nulls_last(),
                PurchaseOrder.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return purchase_orders, total

    def get_purchase_order(
        self,
        db: Session,
        po_id: UUID,
    ) -> Optional[PurchaseOrder]:
        """Get a single purchase order by ID."""
        return (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .options(
                joinedload(PurchaseOrder.line_items).joinedload(
                    PurchaseOrderLineItem.item
                ),
                joinedload(PurchaseOrder.requested_by),
                joinedload(PurchaseOrder.approved_by),
                joinedload(PurchaseOrder.receiving_location),
                joinedload(PurchaseOrder.created_by_user),
                joinedload(PurchaseOrder.supplier),
            )
            .first()
        )

    def get_purchase_order_by_number(
        self,
        db: Session,
        po_number: str,
    ) -> Optional[PurchaseOrder]:
        """Get a purchase order by its number."""
        return (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number == po_number)
            .options(
                joinedload(PurchaseOrder.line_items).joinedload(
                    PurchaseOrderLineItem.item
                ),
                joinedload(PurchaseOrder.requested_by),
                joinedload(PurchaseOrder.approved_by),
                joinedload(PurchaseOrder.receiving_location),
                joinedload(PurchaseOrder.supplier),
            )
            .first()
        )

    def create_purchase_order(
        self,
        db: Session,
        data: PurchaseOrderCreate,
        user_id: UUID,
        request: Optional[Request] = None,
        auto_generated: bool = False,
    ) -> PurchaseOrder:
        """Create a new purchase order."""
        tenant = get_current_tenant()

        supplier = None
        supplier_name = data.supplier_name
        supplier_contact = data.supplier_contact
        supplier_email = data.supplier_email
        supplier_phone = data.supplier_phone

        if data.supplier_id:
            supplier = (
                db.query(Supplier)
                .filter(
                    Supplier.id == data.supplier_id,
                    Supplier.tenant_id == tenant.id,
                )
                .first()
            )

            if not supplier:
                raise ValueError("Supplier not found for this tenant")

            supplier_name = supplier.name
            supplier_contact = supplier.contact_name
            supplier_email = supplier.email
            supplier_phone = supplier.phone

        # Generate PO number
        po_number = self.generate_po_number(db)

        # Create purchase order
        po = PurchaseOrder(
            tenant_id=tenant.id,
            po_number=po_number,
            supplier_id=supplier.id if supplier else None,
            supplier_name=supplier_name,
            supplier_contact=supplier_contact,
            supplier_email=supplier_email,
            supplier_phone=supplier_phone,
            status=PurchaseOrderStatus.DRAFT,
            priority=(
                PurchaseOrderPriority(data.priority)
                if data.priority
                else PurchaseOrderPriority.NORMAL
            ),
            expected_date=data.expected_date,
            receiving_location_id=data.receiving_location_id,
            requested_by_id=data.requested_by_id or user_id,
            notes=data.notes,
            external_reference=data.external_reference,
            auto_generated=auto_generated,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(po)
        db.flush()  # Get the ID

        # Add line items
        subtotal = Decimal("0")
        for item_data in data.line_items:
            line_item = PurchaseOrderLineItem(
                tenant_id=tenant.id,
                purchase_order_id=po.id,
                item_id=item_data.item_id,
                quantity_ordered=item_data.quantity_ordered,
                unit_price=item_data.unit_price,
                line_total=Decimal(str(item_data.quantity_ordered))
                * item_data.unit_price,
                notes=item_data.notes,
            )
            db.add(line_item)
            subtotal += line_item.line_total

        # Update totals
        po.subtotal = subtotal
        po.total_amount = subtotal + po.tax_amount + po.shipping_cost

        db.commit()
        db.refresh(po)

        # Audit log
        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po.po_number,
            action="CREATE",
            user_id=user_id,
            changes={"po_number": po_number, "auto_generated": auto_generated},
            request=request,
        )

        logger.info(f"Created purchase order {po_number}")
        return po

    def update_purchase_order(
        self,
        db: Session,
        po_id: UUID,
        data: PurchaseOrderUpdate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[PurchaseOrder]:
        """Update a purchase order."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return None

        # Only allow updates in certain states
        if po.status not in [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.PENDING_APPROVAL,
        ]:
            raise ValueError(
                f"Cannot update purchase order in {po.status.value} status"
            )

        changes = {}
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(po, field)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}
                setattr(po, field, value)

        if changes:
            po.updated_by = user_id

            # Recalculate total if costs changed
            if "tax_amount" in changes or "shipping_cost" in changes:
                po.total_amount = po.subtotal + po.tax_amount + po.shipping_cost

            db.commit()
            db.refresh(po)

            audit_service.log_action(
                db=db,
                entity_type=EntityType.PURCHASE_ORDER,
                entity_id=po.id,
                entity_name=po.po_number,
                action="UPDATE",
                user_id=user_id,
                changes=changes,
                request=request,
            )

        return po

    def add_line_item(
        self,
        db: Session,
        po_id: UUID,
        item_id: UUID,
        quantity: int,
        unit_price: Decimal,
        user_id: UUID,
        notes: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> Optional[PurchaseOrderLineItem]:
        """Add a line item to a purchase order."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return None

        if po.status not in [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.PENDING_APPROVAL,
        ]:
            raise ValueError(
                f"Cannot add items to purchase order in {po.status.value} status"
            )

        tenant = get_current_tenant()

        line_item = PurchaseOrderLineItem(
            tenant_id=tenant.id,
            purchase_order_id=po_id,
            item_id=item_id,
            quantity_ordered=quantity,
            unit_price=unit_price,
            line_total=Decimal(str(quantity)) * unit_price,
            notes=notes,
        )

        db.add(line_item)

        # Update PO totals
        po.subtotal += line_item.line_total
        po.total_amount = po.subtotal + po.tax_amount + po.shipping_cost
        po.updated_by = user_id

        db.commit()
        db.refresh(line_item)

        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po.po_number,
            action="UPDATE",
            user_id=user_id,
            changes={"added_line_item": str(item_id)},
            request=request,
        )

        return line_item

    def remove_line_item(
        self,
        db: Session,
        po_id: UUID,
        line_item_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> bool:
        """Remove a line item from a purchase order."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return False

        if po.status not in [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.PENDING_APPROVAL,
        ]:
            raise ValueError(
                f"Cannot remove items from purchase order in {po.status.value} status"
            )

        line_item = (
            db.query(PurchaseOrderLineItem)
            .filter(
                PurchaseOrderLineItem.id == line_item_id,
                PurchaseOrderLineItem.purchase_order_id == po_id,
            )
            .first()
        )

        if not line_item:
            return False

        # Update PO totals
        po.subtotal -= line_item.line_total
        po.total_amount = po.subtotal + po.tax_amount + po.shipping_cost
        po.updated_by = user_id

        db.delete(line_item)
        db.commit()

        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po.po_number,
            action="UPDATE",
            user_id=user_id,
            changes={"removed_line_item": str(line_item_id)},
            request=request,
        )

        return True

    def update_status(
        self,
        db: Session,
        po_id: UUID,
        new_status: PurchaseOrderStatus,
        user_id: UUID,
        notes: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> Optional[PurchaseOrder]:
        """Update the status of a purchase order."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return None

        # Validate transition
        valid_transitions = VALID_STATUS_TRANSITIONS.get(po.status, [])
        if new_status not in valid_transitions:
            raise ValueError(
                f"Cannot transition from {po.status.value} to {new_status.value}"
            )

        old_status = po.status
        po.status = new_status
        po.updated_by = user_id

        # Set dates based on status
        if new_status == PurchaseOrderStatus.APPROVED:
            po.approved_by_id = user_id
        elif new_status == PurchaseOrderStatus.ORDERED:
            po.order_date = datetime.utcnow()
        elif new_status == PurchaseOrderStatus.RECEIVED:
            po.received_date = datetime.utcnow()

        # Append notes
        if notes:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            status_note = (
                f"\n[{timestamp}] Status changed to {new_status.value}: {notes}"
            )
            po.notes = (po.notes or "") + status_note

        db.commit()
        db.refresh(po)

        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po.po_number,
            action="STATUS_CHANGE",
            user_id=user_id,
            changes={
                "status": {"old": old_status.value, "new": new_status.value},
                "notes": notes,
            },
            request=request,
        )

        logger.info(
            f"PO {po.po_number} status changed: {old_status.value} -> {new_status.value}"
        )
        return po

    def receive_items(
        self,
        db: Session,
        po_id: UUID,
        receive_data: ReceiveItemsRequest,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[PurchaseOrder]:
        """Receive items on a purchase order and update inventory."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return None

        if po.status not in [
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
        ]:
            raise ValueError(f"Cannot receive items on PO in {po.status.value} status")

        tenant = get_current_tenant()
        received_date = receive_data.received_date or datetime.utcnow()

        for receive_item in receive_data.items:
            line_item = (
                db.query(PurchaseOrderLineItem)
                .filter(
                    PurchaseOrderLineItem.id == receive_item.line_item_id,
                    PurchaseOrderLineItem.purchase_order_id == po_id,
                )
                .first()
            )

            if not line_item:
                continue

            qty_to_receive = receive_item.quantity_received
            max_receivable = line_item.quantity_ordered - line_item.quantity_received

            if qty_to_receive > max_receivable:
                qty_to_receive = max_receivable

            if qty_to_receive <= 0:
                continue

            # Update line item
            line_item.quantity_received += qty_to_receive

            # Update inventory
            item = (
                db.query(InventoryItem)
                .filter(InventoryItem.id == line_item.item_id)
                .first()
            )
            if item:
                old_qty = item.quantity
                item.quantity += qty_to_receive
                item.updated_by = user_id

                # Handle lot creation if lots are specified
                if receive_item.lots:
                    total_lot_qty = 0
                    for received_lot in receive_item.lots:
                        try:
                            lot = lot_service.create_lot(
                                db=db,
                                tenant_id=tenant.id,
                                user_id=user_id,
                                item_id=line_item.item_id,
                                lot_number=received_lot.lot_number,
                                quantity=received_lot.quantity,
                                serial_number=received_lot.serial_number,
                                expiration_date=(
                                    received_lot.expiration_date.date()
                                    if received_lot.expiration_date
                                    else None
                                ),
                                manufacture_date=(
                                    received_lot.manufacture_date.date()
                                    if received_lot.manufacture_date
                                    else None
                                ),
                                location_id=po.receiving_location_id,
                                request=request,
                            )
                            total_lot_qty += received_lot.quantity
                        except ValueError as e:
                            logger.warning(
                                f"Failed to create lot {received_lot.lot_number}: {e}"
                            )
                            # Continue with other lots even if one fails
                            pass

                # Create stock movement
                movement = StockMovement(
                    tenant_id=tenant.id,
                    inventory_item_id=item.id,
                    movement_type=MovementType.RECEIVE,
                    quantity=qty_to_receive,
                    from_location_id=None,
                    to_location_id=po.receiving_location_id,
                    reference_number=f"PO: {po.po_number}",
                    notes=receive_data.notes,
                    created_by=user_id,
                )
                db.add(movement)

                # Update item status
                if item.quantity <= 0:
                    item.status = "out_of_stock"
                elif item.quantity <= item.reorder_point:
                    item.status = "low_stock"
                else:
                    item.status = "in_stock"

        # Determine new PO status
        all_received = all(
            li.quantity_received >= li.quantity_ordered for li in po.line_items
        )
        any_received = any(li.quantity_received > 0 for li in po.line_items)

        if all_received:
            po.status = PurchaseOrderStatus.RECEIVED
            po.received_date = received_date
        elif any_received:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED

        po.updated_by = user_id

        db.commit()
        db.refresh(po)

        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po.po_number,
            action="RECEIVE",
            user_id=user_id,
            changes={"items_received": len(receive_data.items)},
            request=request,
        )

        logger.info(f"Received items on PO {po.po_number}")
        return po

    def delete_purchase_order(
        self,
        db: Session,
        po_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> bool:
        """Delete a purchase order (only in draft status)."""
        po = self.get_purchase_order(db, po_id)
        if not po:
            return False

        if po.status != PurchaseOrderStatus.DRAFT:
            raise ValueError("Can only delete purchase orders in draft status")

        po_number = po.po_number

        audit_service.log_action(
            db=db,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po.id,
            entity_name=po_number,
            action="DELETE",
            user_id=user_id,
            changes={"po_number": po_number},
            request=request,
        )

        db.delete(po)
        db.commit()

        logger.info(f"Deleted purchase order {po_number}")
        return True

    def get_stats(self, db: Session) -> PurchaseOrderStats:
        """Get purchase order statistics."""
        stats = PurchaseOrderStats()

        # Count by status
        status_counts = (
            db.query(PurchaseOrder.status, func.count(PurchaseOrder.id))
            .group_by(PurchaseOrder.status)
            .all()
        )

        for status, count in status_counts:
            stats.total += count
            if status == PurchaseOrderStatus.DRAFT:
                stats.draft = count
            elif status == PurchaseOrderStatus.PENDING_APPROVAL:
                stats.pending_approval = count
            elif status == PurchaseOrderStatus.APPROVED:
                stats.approved = count
            elif status == PurchaseOrderStatus.ORDERED:
                stats.ordered = count
            elif status == PurchaseOrderStatus.PARTIALLY_RECEIVED:
                stats.partially_received = count
            elif status == PurchaseOrderStatus.RECEIVED:
                stats.received = count
            elif status == PurchaseOrderStatus.CANCELLED:
                stats.cancelled = count

        # Count overdue
        now = datetime.utcnow()
        stats.overdue = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.expected_date < now,
                PurchaseOrder.status.notin_(
                    [
                        PurchaseOrderStatus.RECEIVED.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    ]
                ),
            )
            .count()
        )

        # Total value pending (approved + ordered + partially received)
        pending_value = (
            db.query(func.sum(PurchaseOrder.total_amount))
            .filter(
                PurchaseOrder.status.in_(
                    [
                        PurchaseOrderStatus.APPROVED.value,
                        PurchaseOrderStatus.ORDERED.value,
                        PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
                    ]
                )
            )
            .scalar()
        )
        stats.total_value_pending = Decimal(str(pending_value or 0))

        return stats

    def get_low_stock_items(
        self,
        db: Session,
        limit: int = 50,
    ) -> LowStockSuggestion:
        """Get items below reorder point for PO suggestions."""
        # Find items below reorder point
        low_stock = (
            db.query(InventoryItem)
            .filter(
                InventoryItem.quantity <= InventoryItem.reorder_point,
                InventoryItem.reorder_point > 0,
            )
            .order_by((InventoryItem.reorder_point - InventoryItem.quantity).desc())
            .limit(limit)
            .all()
        )

        items = []
        total_estimate = Decimal("0")

        for item in low_stock:
            shortage = item.reorder_point - item.quantity
            # Suggest ordering 2x the shortage or at least to reorder point
            suggested_qty = max(shortage * 2, item.reorder_point)

            low_item = LowStockItem(
                id=item.id,
                name=item.name,
                sku=item.sku,
                current_quantity=item.quantity,
                reorder_point=item.reorder_point,
                unit_price=item.unit_price,
                shortage=shortage,
                suggested_quantity=suggested_qty,
            )
            items.append(low_item)
            total_estimate += Decimal(str(item.unit_price)) * Decimal(
                str(suggested_qty)
            )

        return LowStockSuggestion(
            items=items,
            total_items=len(items),
            estimated_total=total_estimate,
        )

    def create_po_from_low_stock(
        self,
        db: Session,
        item_ids: List[UUID],
        user_id: UUID,
        supplier_name: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> PurchaseOrder:
        """Create a purchase order from selected low stock items."""
        # Get the items
        items = db.query(InventoryItem).filter(InventoryItem.id.in_(item_ids)).all()

        if not items:
            raise ValueError("No valid items provided")

        # Build line items
        from app.schemas.purchase_order import PurchaseOrderLineItemCreate

        line_items = []
        for item in items:
            shortage = max(0, item.reorder_point - item.quantity)
            suggested_qty = max(shortage * 2, item.reorder_point, 1)

            line_items.append(
                PurchaseOrderLineItemCreate(
                    item_id=item.id,
                    quantity_ordered=suggested_qty,
                    unit_price=Decimal(str(item.unit_price)),
                )
            )

        # Create the PO
        po_data = PurchaseOrderCreate(
            supplier_name=supplier_name,
            priority="high",  # Low stock is high priority
            line_items=line_items,
        )

        return self.create_purchase_order(
            db=db,
            data=po_data,
            user_id=user_id,
            request=request,
            auto_generated=True,
        )

    def get_purchase_orders_for_item(
        self,
        db: Session,
        item_id: UUID,
        include_received: bool = False,
    ) -> List[PurchaseOrder]:
        """Get all purchase orders containing a specific item."""
        query = (
            db.query(PurchaseOrder)
            .join(PurchaseOrderLineItem)
            .filter(PurchaseOrderLineItem.item_id == item_id)
            .options(joinedload(PurchaseOrder.requested_by))
        )

        if not include_received:
            query = query.filter(
                PurchaseOrder.status.notin_(
                    [
                        PurchaseOrderStatus.RECEIVED.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    ]
                )
            )

        return query.order_by(PurchaseOrder.created_at.desc()).all()


# Singleton instance
purchase_order_service = PurchaseOrderService()
