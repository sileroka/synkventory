"""
Service layer for Stock Movements: receive, ship, transfer, adjust, count.

Centralizes inventory quantity updates, lot quantity handling, and audit logging.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func

from app.core.tenant import get_current_tenant
from app.models.audit_log import AuditAction
from app.models.inventory import InventoryItem as InventoryItemModel
from app.models.inventory_location_quantity import (
    InventoryLocationQuantity as InventoryLocationQuantityModel,
)
from app.models.stock_movement import StockMovement as StockMovementModel, MovementType
from app.models.item_consumption import ItemConsumption, ConsumptionSource
from app.schemas.stock_movement import (
    StockMovementCreate,
    MovementType as MovementTypeSchema,
)
from app.services.audit import audit_service
from app.services.lot import lot_service


def _update_inventory_status(item: InventoryItemModel) -> None:
    if item.quantity <= 0:
        item.status = "out_of_stock"
    elif item.quantity <= item.reorder_point:
        item.status = "low_stock"
    else:
        item.status = "in_stock"


def _recalculate_total_quantity(db: Session, inventory_item_id: str) -> int:
    result = (
        db.query(
            sql_func.coalesce(sql_func.sum(InventoryLocationQuantityModel.quantity), 0)
        )
        .filter(InventoryLocationQuantityModel.inventory_item_id == inventory_item_id)
        .scalar()
    )
    return int(result or 0)


def _get_or_create_location_quantity(
    db: Session, inventory_item_id: str, location_id: str
) -> InventoryLocationQuantityModel:
    loc_qty = (
        db.query(InventoryLocationQuantityModel)
        .filter(
            InventoryLocationQuantityModel.inventory_item_id == inventory_item_id,
            InventoryLocationQuantityModel.location_id == location_id,
        )
        .first()
    )
    if not loc_qty:
        loc_qty = InventoryLocationQuantityModel(
            inventory_item_id=inventory_item_id,
            location_id=location_id,
            quantity=0,
        )
        db.add(loc_qty)
        db.flush()
    return loc_qty


class StockMovementService:
    """Encapsulates stock movement side effects and auditing."""

    def create_movement(
        self,
        db: Session,
        movement: StockMovementCreate,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> StockMovementModel:
        tenant = get_current_tenant()
        if not tenant:
            raise HTTPException(status_code=400, detail="Tenant context required")

        item = (
            db.query(InventoryItemModel)
            .filter(InventoryItemModel.id == movement.inventory_item_id)
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        old_quantity = item.quantity

        # Validate movement-specific requirements
        if movement.movement_type == MovementTypeSchema.TRANSFER:
            if not movement.from_location_id or not movement.to_location_id:
                raise HTTPException(
                    status_code=400,
                    detail="Transfer movements require both from_location_id and to_location_id",
                )
            if movement.quantity <= 0:
                raise HTTPException(
                    status_code=400, detail="Transfer quantity must be positive"
                )

        if movement.movement_type in [
            MovementTypeSchema.RECEIVE,
            MovementTypeSchema.COUNT,
        ]:
            if not movement.to_location_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"{movement.movement_type.value} movements require to_location_id",
                )
        elif movement.movement_type == MovementTypeSchema.SHIP:
            if not movement.from_location_id:
                raise HTTPException(
                    status_code=400, detail="Ship movements require from_location_id"
                )
        elif movement.movement_type == MovementTypeSchema.ADJUST:
            if movement.quantity > 0 and not movement.to_location_id:
                raise HTTPException(
                    status_code=400,
                    detail="Positive adjustments require to_location_id",
                )
            if movement.quantity < 0 and not movement.from_location_id:
                raise HTTPException(
                    status_code=400,
                    detail="Negative adjustments require from_location_id",
                )

        # Update per-location quantities
        if movement.movement_type == MovementTypeSchema.TRANSFER:
            from_loc_qty = _get_or_create_location_quantity(
                db, movement.inventory_item_id, movement.from_location_id
            )
            if from_loc_qty.quantity < movement.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity at source location. Available: {from_loc_qty.quantity}",
                )
            from_loc_qty.quantity -= movement.quantity
            from_loc_qty.updated_at = datetime.utcnow()

            to_loc_qty = _get_or_create_location_quantity(
                db, movement.inventory_item_id, movement.to_location_id
            )
            to_loc_qty.quantity += movement.quantity
            to_loc_qty.updated_at = datetime.utcnow()

        elif movement.from_location_id and movement.quantity < 0:
            from_loc_qty = _get_or_create_location_quantity(
                db, movement.inventory_item_id, movement.from_location_id
            )
            new_loc_qty = from_loc_qty.quantity + movement.quantity  # negative
            if new_loc_qty < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity at location. Available: {from_loc_qty.quantity}",
                )
            from_loc_qty.quantity = new_loc_qty
            from_loc_qty.updated_at = datetime.utcnow()

        elif movement.to_location_id and movement.quantity > 0:
            to_loc_qty = _get_or_create_location_quantity(
                db, movement.inventory_item_id, movement.to_location_id
            )
            to_loc_qty.quantity += movement.quantity
            to_loc_qty.updated_at = datetime.utcnow()

        # Lot updates
        lot_id = None
        if movement.lot_id:
            lot_id = (
                UUID(movement.lot_id)
                if isinstance(movement.lot_id, str)
                else movement.lot_id
            )

        if movement.movement_type == MovementTypeSchema.RECEIVE and lot_id:
            lot = lot_service.get_lot_by_id(db, lot_id)
            if not lot:
                raise HTTPException(status_code=404, detail="Specified lot not found")
            lot.quantity += movement.quantity
            lot.updated_by = user_id
            db.flush()
        elif lot_id and movement.movement_type in [
            MovementTypeSchema.SHIP,
            MovementTypeSchema.TRANSFER,
        ]:
            lot = lot_service.get_lot_by_id(db, lot_id)
            if not lot:
                raise HTTPException(status_code=404, detail="Specified lot not found")
            decrement_qty = abs(movement.quantity)
            if lot.quantity < decrement_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity in lot. Available: {lot.quantity}",
                )
            lot.quantity -= decrement_qty
            lot.updated_by = user_id
            if (
                movement.movement_type == MovementTypeSchema.TRANSFER
                and movement.to_location_id
            ):
                lot.location_id = (
                    UUID(movement.to_location_id)
                    if isinstance(movement.to_location_id, str)
                    else movement.to_location_id
                )
            db.flush()

        # Create movement record
        db_movement = StockMovementModel(
            inventory_item_id=movement.inventory_item_id,
            movement_type=MovementType(movement.movement_type.value),
            quantity=movement.quantity,
            from_location_id=movement.from_location_id,
            to_location_id=movement.to_location_id,
            lot_id=lot_id,
            reference_number=movement.reference_number,
            notes=movement.notes,
            tenant_id=tenant.id,
            created_by=user_id,
        )
        db.add(db_movement)

        # Record consumption for negative, non-transfer movements
        if movement.quantity < 0 and movement.movement_type in [
            MovementTypeSchema.SHIP,
            MovementTypeSchema.ADJUST,
            MovementTypeSchema.COUNT,
        ]:
            source_map = {
                MovementTypeSchema.SHIP: ConsumptionSource.SALES_ORDER,
                MovementTypeSchema.ADJUST: ConsumptionSource.ADJUSTMENT,
                MovementTypeSchema.COUNT: ConsumptionSource.ADJUSTMENT,
            }
            today = datetime.utcnow().date()
            # Aggregate multiple movements on same date to a single record per item
            existing = (
                db.query(ItemConsumption)
                .filter(
                    ItemConsumption.tenant_id == tenant.id,
                    ItemConsumption.item_id == movement.inventory_item_id,
                    ItemConsumption.date == today,
                )
                .first()
            )
            add_qty = Decimal(abs(movement.quantity))
            if existing:
                existing.quantity = (existing.quantity or Decimal(0)) + add_qty
                existing.source = source_map.get(
                    movement.movement_type, existing.source or ConsumptionSource.OTHER
                )
                existing.updated_by = user_id
                existing.updated_at = datetime.utcnow()
            else:
                consumption = ItemConsumption(
                    tenant_id=tenant.id,
                    item_id=movement.inventory_item_id,
                    date=today,
                    quantity=add_qty,
                    source=source_map.get(
                        movement.movement_type, ConsumptionSource.OTHER
                    ),
                    created_by=user_id,
                    updated_by=user_id,
                )
                db.add(consumption)

        # Recalculate item total and update status
        item.quantity = _recalculate_total_quantity(db, movement.inventory_item_id)
        item.updated_at = datetime.utcnow()
        _update_inventory_status(item)

        db.commit()
        db.refresh(db_movement)

        # Audit mapping
        movement_type_to_audit_action = {
            MovementTypeSchema.RECEIVE: AuditAction.STOCK_RECEIVE,
            MovementTypeSchema.SHIP: AuditAction.STOCK_SHIP,
            MovementTypeSchema.TRANSFER: AuditAction.STOCK_TRANSFER,
            MovementTypeSchema.ADJUST: AuditAction.STOCK_ADJUST,
            MovementTypeSchema.COUNT: AuditAction.STOCK_COUNT,
        }
        audit_action = movement_type_to_audit_action.get(
            movement.movement_type, AuditAction.STOCK_ADJUST
        )

        audit_service.log_stock_movement(
            db=db,
            tenant_id=tenant.id,
            user_id=user_id,
            movement_type=audit_action,
            item_id=item.id,
            item_name=f"{item.sku} - {item.name}",
            quantity_change=movement.quantity,
            old_quantity=old_quantity,
            new_quantity=item.quantity,
            from_location_id=movement.from_location_id,
            to_location_id=movement.to_location_id,
            reference_number=movement.reference_number,
            reason=movement.notes,
            request=request,
        )

        # Reload with relationships for consistency
        db_movement = (
            db.query(StockMovementModel)
            .options(
                joinedload(StockMovementModel.inventory_item),
                joinedload(StockMovementModel.from_location),
                joinedload(StockMovementModel.to_location),
            )
            .filter(StockMovementModel.id == db_movement.id)
            .first()
        )

        return db_movement


stock_movement_service = StockMovementService()
