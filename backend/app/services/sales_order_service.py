"""
Service layer for Sales Order operations.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import uuid

from fastapi import Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case

from app.core.tenant import get_current_tenant
from app.models.audit_log import EntityType
from app.models.customer import Customer
from app.models.inventory import InventoryItem
from app.models.sales_order import (
    SalesOrder,
    SalesOrderLineItem,
    SalesOrderStatus,
    SalesOrderPriority,
)
from app.services.audit import audit_service

logger = logging.getLogger(__name__)


VALID_STATUS_TRANSITIONS = {
    SalesOrderStatus.DRAFT: [SalesOrderStatus.CONFIRMED, SalesOrderStatus.CANCELLED],
    SalesOrderStatus.CONFIRMED: [SalesOrderStatus.PICKED, SalesOrderStatus.CANCELLED],
    SalesOrderStatus.PICKED: [SalesOrderStatus.SHIPPED, SalesOrderStatus.CANCELLED],
    SalesOrderStatus.SHIPPED: [],
    SalesOrderStatus.CANCELLED: [],
}


class SalesOrderService:
    """Service for managing sales orders."""

    def generate_so_number(self, db: Session) -> str:
        """Generate a unique sales order number."""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"SO-{today}-"

        latest = (
            db.query(SalesOrder)
            .filter(SalesOrder.order_number.like(f"{prefix}%"))
            .order_by(SalesOrder.order_number.desc())
            .first()
        )

        if latest:
            try:
                last_num = int(latest.order_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def get_sales_orders(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 25,
        status: Optional[SalesOrderStatus] = None,
        priority: Optional[SalesOrderPriority] = None,
        customer_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[SalesOrder], int]:
        """Get paginated list of sales orders."""
        query = db.query(SalesOrder).options(
            joinedload(SalesOrder.customer),
        )
        if status:
            query = query.filter(SalesOrder.status == status)

        if priority:
            query = query.filter(SalesOrder.priority == priority)

        if customer_id:
            query = query.filter(SalesOrder.customer_id == str(customer_id))

        if start_date:
            query = query.filter(SalesOrder.order_date >= start_date)
        if end_date:
            query = query.filter(SalesOrder.order_date <= end_date)

        if status:
            query = query.filter(SalesOrder.status == status)

        if priority:
            query = query.filter(SalesOrder.priority == priority)

        if customer_id:
            query = query.filter(SalesOrder.customer_id == str(customer_id))

        total = query.count()

        sales_orders = (
            query.order_by(
                case(
                    (SalesOrder.priority == SalesOrderPriority.HIGH.value, 0),
                    (SalesOrder.priority == SalesOrderPriority.NORMAL.value, 1),
                    (SalesOrder.priority == SalesOrderPriority.LOW.value, 2),
                ),
                SalesOrder.expected_ship_date.asc().nulls_last(),
                SalesOrder.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return sales_orders, total

    def get_sales_order(self, db: Session, so_id: UUID) -> Optional[SalesOrder]:
        """Get a single sales order by ID."""
        return (
            db.query(SalesOrder)
            .filter(SalesOrder.id == str(so_id))
            .options(
                joinedload(SalesOrder.line_items).joinedload(SalesOrderLineItem.item),
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.created_by_user),
            )
            .first()
        )

    def create_sales_order(
        self,
        db: Session,
        data,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> SalesOrder:
        """Create a new sales order with line items."""
        tenant = get_current_tenant()

        customer = None
        if getattr(data, "customer_id", None):
            customer = (
                db.query(Customer)
                .filter(
                    Customer.id == str(data.customer_id),
                    Customer.tenant_id == str(tenant.id),
                )
                .first()
            )
            if not customer:
                raise ValueError("Customer not found for this tenant")

        order_number = self.generate_so_number(db)

        so = SalesOrder(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            order_number=order_number,
            customer_id=(str(customer.id) if customer else None),
            status=SalesOrderStatus.DRAFT,
            priority=(
                SalesOrderPriority(data.priority)
                if data.priority
                else SalesOrderPriority.NORMAL
            ),
            order_date=data.order_date,
            expected_ship_date=data.expected_ship_date,
            notes=data.notes,
            created_by=str(user_id),
            updated_by=str(user_id),
        )

        db.add(so)
        db.flush()

        subtotal = Decimal("0")
        for li in data.line_items:
            line = SalesOrderLineItem(
                id=str(uuid.uuid4()),
                tenant_id=str(tenant.id),
                sales_order=so,
                item_id=str(li.item_id) if li.item_id is not None else None,
                quantity_ordered=li.quantity_ordered,
                unit_price=li.unit_price,
                line_total=Decimal(str(li.quantity_ordered)) * li.unit_price,
                notes=li.notes,
            )
            db.add(line)
            subtotal += line.line_total

        so.subtotal = subtotal
        so.total_amount = subtotal + so.tax_amount + so.shipping_cost

        db.commit()
        db.refresh(so)

        audit_service.log_create(
            db=db,
            tenant_id=uuid.UUID(str(tenant.id)) if isinstance(tenant.id, uuid.UUID) else tenant.id,  # safe tenant
            user_id=user_id,
            entity_type=EntityType.SALES_ORDER,
            entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
            entity_name=so.order_number,
            data={"order_number": order_number},
            request=request,
        )

        logger.info(f"Created sales order {order_number}")
        return so

    def update_sales_order(
        self,
        db: Session,
        so_id: UUID,
        data,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[SalesOrder]:
        """Update a sales order in mutable states."""
        # Fetch directly to avoid any aliasing issues during tests
        so = (
            db.query(SalesOrder)
            .filter(SalesOrder.id == str(so_id))
            .options(
                joinedload(SalesOrder.line_items).joinedload(SalesOrderLineItem.item),
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.created_by_user),
            )
            .first()
        )
        if not so:
            return None

        if so.status not in [SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED]:
            raise ValueError(f"Cannot update sales order in {so.status.value} status")

        changes = {}
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            old = getattr(so, field)
            if old != value:
                changes[field] = {"old": str(old), "new": str(value)}
                setattr(so, field, value)

        if changes:
            so.updated_by = user_id
            if "tax_amount" in changes or "shipping_cost" in changes:
                so.total_amount = so.subtotal + so.tax_amount + so.shipping_cost

            db.commit()
            db.refresh(so)

            audit_service.log_update(
                db=db,
                tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
                user_id=user_id,
                entity_type=EntityType.SALES_ORDER,
                entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
                entity_name=so.order_number,
                changes=changes,
                request=request,
            )

        return so

    def update_status(
        self,
        db: Session,
        so_id: UUID,
        new_status: SalesOrderStatus,
        user_id: UUID,
        notes: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> Optional[SalesOrder]:
        # Fetch directly to avoid aliasing/type issues (SQLite tests store UUIDs as strings)
        so = (
            db.query(SalesOrder)
            .filter(SalesOrder.id == str(so_id))
            .options(
                joinedload(SalesOrder.line_items).joinedload(SalesOrderLineItem.item),
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.created_by_user),
            )
            .first()
        )
        if not so:
            return None

        # Validate transition
        allowed = VALID_STATUS_TRANSITIONS.get(so.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid status transition from {so.status.value} to {new_status.value}")

        old_status = so.status
        so.status = new_status

        # Set timestamps for terminal states
        now = datetime.utcnow()
        if new_status == SalesOrderStatus.SHIPPED:
            so.shipped_date = now
        if new_status == SalesOrderStatus.CANCELLED:
            so.cancelled_date = now

        so.updated_by = str(user_id)
        db.commit()
        db.refresh(so)

        # Audit
        changes = {"status": {"old": old_status.value, "new": new_status.value}}
        if notes:
            changes["notes"] = {"old": None, "new": notes}
        audit_service.log_update(
            db=db,
            tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
            user_id=user_id,
            entity_type=EntityType.SALES_ORDER,
            entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
            entity_name=so.order_number,
            changes=changes,
            request=request,
        )

        return so

    def add_line_item(
        self,
        db: Session,
        sales_order_id: UUID,
        item_id: UUID,
        quantity: int,
        unit_price: Decimal,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[SalesOrder]:
        """Add a line item to a sales order while in Draft or Confirmed."""
        so = self.get_sales_order(db, sales_order_id)
        if not so:
            return None
        if so.status not in [SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED]:
            raise ValueError(f"Cannot add line items in {so.status.value} status")

        line = SalesOrderLineItem(
            id=str(uuid.uuid4()),
            tenant_id=str(so.tenant_id),
            sales_order=so,
            item_id=str(item_id),
            quantity_ordered=quantity,
            unit_price=unit_price,
            line_total=Decimal(str(quantity)) * unit_price,
            notes=None,
        )
        db.add(line)
        db.flush()

        # Recompute totals
        so.subtotal = sum((li.line_total or Decimal("0")) for li in (so.line_items or []))
        so.total_amount = so.subtotal + (so.tax_amount or 0) + (so.shipping_cost or 0)
        so.updated_by = str(user_id)
        db.commit()
        db.refresh(so)

        # Audit
        audit_service.log_update(
            db=db,
            tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
            user_id=user_id,
            entity_type=EntityType.SALES_ORDER,
            entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
            entity_name=so.order_number,
            changes={
                "add_line_item": {
                    "item_id": str(item_id),
                    "quantity": quantity,
                    "unit_price": str(unit_price),
                }
            },
            request=request,
        )

        return so

    def remove_line_item(
        self,
        db: Session,
        sales_order_id: UUID,
        line_item_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[SalesOrder]:
        """Remove a line item from a sales order while in Draft or Confirmed."""
        so = self.get_sales_order(db, sales_order_id)
        if not so:
            return None
        if so.status not in [SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED]:
            raise ValueError(f"Cannot remove line items in {so.status.value} status")

        li = next((x for x in (so.line_items or []) if str(x.id) == str(line_item_id)), None)
        if not li:
            return None

        db.delete(li)
        db.flush()

        # Recompute totals
        so.subtotal = sum((x.line_total or Decimal("0")) for x in (so.line_items or []))
        so.total_amount = so.subtotal + (so.tax_amount or 0) + (so.shipping_cost or 0)
        so.updated_by = str(user_id)
        db.commit()
        db.refresh(so)

        # Audit
        audit_service.log_update(
            db=db,
            tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
            user_id=user_id,
            entity_type=EntityType.SALES_ORDER,
            entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
            entity_name=so.order_number,
            changes={"remove_line_item": {"line_item_id": str(line_item_id)}},
            request=request,
        )

        return so

    def ship_items(
        self,
        db: Session,
        sales_order_id: UUID,
        shipments: List[dict],
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[SalesOrder]:
        """
        Ship items on a sales order.

        shipments: List of {"lineItemId": UUID, "quantity": int, optional keys: "fromLocationId", "lotId"}
        Decrements inventory, creates stock movements of type 'ship', updates quantity_shipped.
        Marks order as Shipped when all quantities are shipped.
        """
        from app.models.stock_movement import StockMovement, MovementType
        from app.models.inventory import InventoryItem

        so = self.get_sales_order(db, sales_order_id)
        if not so:
            return None
        if so.status not in [SalesOrderStatus.CONFIRMED, SalesOrderStatus.PICKED]:
            raise ValueError(f"Cannot ship items in {so.status.value} status")

        shipped_any = False

        for entry in shipments:
            li_id = str(entry.get("lineItemId") or entry.get("line_item_id"))
            qty = int(entry.get("quantity", 0))
            from_loc = entry.get("fromLocationId") or entry.get("from_location_id")
            lot_id = entry.get("lotId") or entry.get("lot_id")

            li = next((x for x in (so.line_items or []) if str(x.id) == li_id), None)
            if not li or qty <= 0:
                continue

            remaining = max(0, li.quantity_ordered - li.quantity_shipped)
            ship_qty = min(remaining, qty)
            if ship_qty <= 0:
                continue

            # Decrement inventory
            item = db.query(InventoryItem).filter(InventoryItem.id == str(li.item_id)).first()
            if item:
                item.quantity = max(0, (item.quantity or 0) - ship_qty)

            # Update line item shipped quantity
            li.quantity_shipped = (li.quantity_shipped or 0) + ship_qty

            # Create stock movement
            sm = StockMovement(
                id=str(uuid.uuid4()),
                tenant_id=str(so.tenant_id),
                inventory_item_id=str(li.item_id),
                movement_type=MovementType.SHIP,
                quantity=-ship_qty,
                from_location_id=str(from_loc) if from_loc else None,
                to_location_id=None,
                lot_id=str(lot_id) if lot_id else None,
                reference_number=so.order_number,
                notes=f"SO {so.order_number} shipment",
                created_by=str(user_id),
            )
            db.add(sm)

            # Audit stock movement
            audit_service.log_stock_movement(
                db=db,
                tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
                user_id=user_id,
                movement_type="STOCK_SHIP",
                item_id=UUID(str(li.item_id)),
                item_name=item.name if item else None,
                quantity_change=-ship_qty,
                old_quantity=(item.quantity + ship_qty) if item else 0,
                new_quantity=item.quantity if item else 0,
                from_location_id=UUID(str(from_loc)) if from_loc else None,
                to_location_id=None,
                reference_number=so.order_number,
                reason="Sales order shipment",
                request=request,
            )

            shipped_any = True

        if shipped_any:
            # If all items shipped, mark order as shipped
            all_shipped = all(
                (li.quantity_shipped or 0) >= (li.quantity_ordered or 0)
                for li in (so.line_items or [])
            )
            if all_shipped:
                so.status = SalesOrderStatus.SHIPPED
                so.shipped_date = datetime.utcnow()
            so.updated_by = str(user_id)
            db.commit()
            db.refresh(so)

            audit_service.log_update(
                db=db,
                tenant_id=uuid.UUID(str(so.tenant_id)) if not isinstance(so.tenant_id, UUID) else so.tenant_id,
                user_id=user_id,
                entity_type=EntityType.SALES_ORDER,
                entity_id=UUID(str(so.id)) if not isinstance(so.id, UUID) else so.id,
                entity_name=so.order_number,
                changes={"shipment": {"line_items": len(shipments), "status": so.status.value}},
                request=request,
            )

        return so


sales_order_service = SalesOrderService()