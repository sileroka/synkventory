"""
Item Lot service for managing serial/lot/batch tracking.

This service provides business logic for:
- Creating and managing item lots with expiration dates
- Tracking serial numbers and batch information
- Validating lot quantities and location assignment
- Recording audit logs for lot operations
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.item_lot import ItemLot
from app.models.inventory import InventoryItem
from app.models.location import Location
from app.models.audit_log import AuditAction, EntityType
from app.services.audit import audit_service

logger = logging.getLogger(__name__)


class LotService:
    """Service for item lot operations."""

    def get_lots(
        self,
        db: Session,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        include_expired: bool = False,
        order_by: str = "created_at",
    ) -> List[ItemLot]:
        """
        Get lots with optional filters.

        Args:
            db: Database session
            item_id: Filter by specific item
            location_id: Filter by storage location
            include_expired: Include expired lots (default False)
            order_by: Field to order by (created_at, expiration_date, lot_number)

        Returns:
            List of ItemLot entries matching filters
        """
        from datetime import date

        query = db.query(ItemLot).options(
            joinedload(ItemLot.item),
            joinedload(ItemLot.location),
        )

        if item_id:
            query = query.filter(ItemLot.item_id == item_id)

        if location_id:
            query = query.filter(ItemLot.location_id == location_id)

        if not include_expired:
            query = query.filter(
                or_(
                    ItemLot.expiration_date == None,
                    ItemLot.expiration_date >= date.today(),
                )
            )

        # Order by specified field
        if order_by == "expiration_date":
            query = query.order_by(ItemLot.expiration_date)
        elif order_by == "lot_number":
            query = query.order_by(ItemLot.lot_number)
        else:  # default to created_at
            query = query.order_by(ItemLot.created_at)

        return query.all()

    def get_lot_by_id(self, db: Session, lot_id: UUID) -> Optional[ItemLot]:
        """
        Get a single lot by ID.

        Args:
            db: Database session
            lot_id: Lot ID to retrieve

        Returns:
            ItemLot or None if not found
        """
        return (
            db.query(ItemLot)
            .filter(ItemLot.id == lot_id)
            .options(
                joinedload(ItemLot.item),
                joinedload(ItemLot.location),
            )
            .first()
        )

    def create_lot(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        item_id: UUID,
        lot_number: str,
        quantity: int,
        serial_number: Optional[str] = None,
        expiration_date: Optional[str] = None,
        manufacture_date: Optional[str] = None,
        location_id: Optional[UUID] = None,
        request: Optional[Request] = None,
    ) -> ItemLot:
        """
        Create a new item lot.

        Validates:
        - Item exists
        - Quantity is positive
        - Lot number is unique per tenant
        - Location exists (if specified)

        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID creating the lot
            item_id: Parent inventory item ID
            lot_number: Unique lot identifier
            quantity: Quantity of items in lot
            serial_number: Optional serial number for single-unit items
            expiration_date: Optional expiration date (ISO format)
            manufacture_date: Optional manufacture date (ISO format)
            location_id: Optional location where lot is stored
            request: FastAPI request for audit context

        Returns:
            Created ItemLot

        Raises:
            ValueError: If validation fails
        """
        # Validate item exists
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise ValueError("Inventory item not found")

        # Validate quantity
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        # Check for duplicate lot number per tenant
        existing = (
            db.query(ItemLot)
            .filter(
                and_(
                    ItemLot.tenant_id == tenant_id,
                    ItemLot.lot_number == lot_number,
                )
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Lot number '{lot_number}' already exists for this tenant"
            )

        # Validate location exists (if specified)
        if location_id:
            location = db.query(Location).filter(Location.id == location_id).first()
            if not location:
                raise ValueError("Location not found")

        # Create lot
        lot = ItemLot(
            tenant_id=tenant_id,
            item_id=item_id,
            lot_number=lot_number,
            serial_number=serial_number,
            quantity=quantity,
            expiration_date=expiration_date,
            manufacture_date=manufacture_date,
            location_id=location_id,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(lot)
        db.commit()
        db.refresh(lot)

        # Log audit entry
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=lot.id,
            entity_name=f"Lot {lot_number}",
            changes={
                "lot_number": lot_number,
                "quantity": quantity,
                "item_id": str(item_id),
                "location_id": str(location_id) if location_id else None,
            },
            extra_data={"entity_subtype": "ITEM_LOT"},
            request=request,
        )

        logger.info(
            f"Created lot {lot_number} for item {item.name} with quantity {quantity}"
        )

        return lot

    def update_lot(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        lot_id: UUID,
        lot_number: Optional[str] = None,
        serial_number: Optional[str] = None,
        quantity: Optional[int] = None,
        expiration_date: Optional[str] = None,
        manufacture_date: Optional[str] = None,
        location_id: Optional[UUID] = None,
        request: Optional[Request] = None,
    ) -> ItemLot:
        """
        Update an existing item lot.

        Validates:
        - Lot exists
        - Quantity is positive (if provided)
        - New lot number is unique (if changing)
        - Location exists (if provided)

        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID performing update
            lot_id: Lot ID to update
            lot_number: New lot number (optional)
            serial_number: New serial number (optional)
            quantity: New quantity (optional)
            expiration_date: New expiration date (optional)
            manufacture_date: New manufacture date (optional)
            location_id: New location (optional)
            request: FastAPI request for audit context

        Returns:
            Updated ItemLot

        Raises:
            ValueError: If validation fails
        """
        lot = db.query(ItemLot).filter(ItemLot.id == lot_id).first()
        if not lot:
            raise ValueError("Lot not found")

        changes = {}

        # Validate and update lot number
        if lot_number is not None and lot_number != lot.lot_number:
            existing = (
                db.query(ItemLot)
                .filter(
                    and_(
                        ItemLot.tenant_id == tenant_id,
                        ItemLot.lot_number == lot_number,
                        ItemLot.id != lot_id,  # Exclude current lot
                    )
                )
                .first()
            )
            if existing:
                raise ValueError(
                    f"Lot number '{lot_number}' already exists for this tenant"
                )
            changes["lot_number"] = {"old": lot.lot_number, "new": lot_number}
            lot.lot_number = lot_number

        # Update serial number
        if serial_number is not None:
            changes["serial_number"] = {"old": lot.serial_number, "new": serial_number}
            lot.serial_number = serial_number

        # Validate and update quantity
        if quantity is not None and quantity != lot.quantity:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")
            changes["quantity"] = {"old": lot.quantity, "new": quantity}
            lot.quantity = quantity

        # Update dates
        if expiration_date is not None:
            changes["expiration_date"] = {
                "old": lot.expiration_date,
                "new": expiration_date,
            }
            lot.expiration_date = expiration_date

        if manufacture_date is not None:
            changes["manufacture_date"] = {
                "old": lot.manufacture_date,
                "new": manufacture_date,
            }
            lot.manufacture_date = manufacture_date

        # Validate and update location
        if location_id is not None and location_id != lot.location_id:
            if location_id:
                location = db.query(Location).filter(Location.id == location_id).first()
                if not location:
                    raise ValueError("Location not found")
            changes["location_id"] = {
                "old": str(lot.location_id) if lot.location_id else None,
                "new": str(location_id) if location_id else None,
            }
            lot.location_id = location_id

        lot.updated_by = user_id

        db.commit()
        db.refresh(lot)

        # Log audit entry if changes were made
        if changes:
            audit_service.log(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                entity_type=EntityType.INVENTORY_ITEM,
                entity_id=lot.id,
                entity_name=f"Lot {lot.lot_number}",
                changes=changes,
                extra_data={"entity_subtype": "ITEM_LOT"},
                request=request,
            )

        logger.info(
            f"Updated lot {lot.lot_number} with changes: {list(changes.keys())}"
        )

        return lot

    def delete_lot(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        lot_id: UUID,
        request: Optional[Request] = None,
    ) -> None:
        """
        Delete an item lot.

        Removes the lot from inventory tracking. The parent item's
        total_quantity will be recalculated automatically.

        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID performing deletion
            lot_id: Lot ID to delete
            request: FastAPI request for audit context

        Raises:
            ValueError: If lot not found
        """
        lot = (
            db.query(ItemLot)
            .filter(ItemLot.id == lot_id)
            .options(joinedload(ItemLot.item))
            .first()
        )

        if not lot:
            raise ValueError("Lot not found")

        lot_number = lot.lot_number
        item_name = lot.item.name if lot.item else "Unknown"
        quantity = lot.quantity

        db.delete(lot)
        db.commit()

        # Log audit entry
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=lot_id,
            entity_name=f"Lot {lot_number}",
            changes={"quantity_removed": quantity, "item": item_name},
            extra_data={"entity_subtype": "ITEM_LOT"},
            request=request,
        )

        logger.info(f"Deleted lot {lot_number} ({quantity} units) for item {item_name}")


# Service instance
lot_service = LotService()
