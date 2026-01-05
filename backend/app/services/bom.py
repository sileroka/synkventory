"""
Bill of Materials service for managing item compositions and build operations.

This service provides business logic for:
- Managing BOM component entries
- Calculating build availability
- Performing build and unbuild operations
- Tracking component usage (where-used queries)
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.bill_of_material import BillOfMaterial
from app.models.inventory import InventoryItem
from app.models.stock_movement import StockMovement, MovementType
from app.models.audit_log import AuditAction, EntityType
from app.services.audit import audit_service
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class BOMService:
    """Service for Bill of Materials operations."""

    def get_bom_components(
        self,
        db: Session,
        parent_item_id: UUID,
    ) -> List[BillOfMaterial]:
        """
        Get all components for a parent item's BOM.
        
        Args:
            db: Database session
            parent_item_id: The parent/assembly item ID
            
        Returns:
            List of BillOfMaterial entries with component details
        """
        bom_entries = (
            db.query(BillOfMaterial)
            .filter(BillOfMaterial.parent_item_id == parent_item_id)
            .options(joinedload(BillOfMaterial.component_item))
            .order_by(BillOfMaterial.display_order, BillOfMaterial.created_at)
            .all()
        )
        
        # Add image URLs to component items
        for entry in bom_entries:
            if entry.component_item and entry.component_item.image_key:
                entry.component_item.image_url = storage_service.get_signed_url(
                    entry.component_item.image_key
                )
            elif entry.component_item:
                entry.component_item.image_url = None
        
        return bom_entries

    def get_where_used(
        self,
        db: Session,
        component_item_id: UUID,
    ) -> List[BillOfMaterial]:
        """
        Get all assemblies where a component is used.
        
        Args:
            db: Database session
            component_item_id: The component item ID
            
        Returns:
            List of BillOfMaterial entries showing where component is used
        """
        bom_entries = (
            db.query(BillOfMaterial)
            .filter(BillOfMaterial.component_item_id == component_item_id)
            .options(joinedload(BillOfMaterial.parent_item))
            .order_by(BillOfMaterial.created_at)
            .all()
        )
        
        # Add image URLs to parent items
        for entry in bom_entries:
            if entry.parent_item and entry.parent_item.image_key:
                entry.parent_item.image_url = storage_service.get_signed_url(
                    entry.parent_item.image_key
                )
            elif entry.parent_item:
                entry.parent_item.image_url = None
        
        return bom_entries

    def create_bom_entry(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        parent_item_id: UUID,
        component_item_id: UUID,
        quantity_required: int,
        unit_of_measure: Optional[str] = "units",
        notes: Optional[str] = None,
        display_order: Optional[int] = 0,
        request: Optional[Request] = None,
    ) -> BillOfMaterial:
        """
        Create a new BOM component entry.
        
        Validates:
        - Parent and component items exist
        - No circular references
        - No duplicate entries
        """
        # Validate parent item exists
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == parent_item_id
        ).first()
        if not parent_item:
            raise ValueError("Parent item not found")
        
        # Validate component item exists
        component_item = db.query(InventoryItem).filter(
            InventoryItem.id == component_item_id
        ).first()
        if not component_item:
            raise ValueError("Component item not found")
        
        # Prevent self-reference
        if parent_item_id == component_item_id:
            raise ValueError("An item cannot be a component of itself")
        
        # Check for circular references
        if self._would_create_cycle(db, parent_item_id, component_item_id):
            raise ValueError("Adding this component would create a circular reference")
        
        # Check for duplicate entry
        existing = db.query(BillOfMaterial).filter(
            and_(
                BillOfMaterial.parent_item_id == parent_item_id,
                BillOfMaterial.component_item_id == component_item_id,
            )
        ).first()
        if existing:
            raise ValueError("This component is already in the BOM")
        
        # Create BOM entry
        bom_entry = BillOfMaterial(
            tenant_id=tenant_id,
            parent_item_id=parent_item_id,
            component_item_id=component_item_id,
            quantity_required=quantity_required,
            unit_of_measure=unit_of_measure,
            notes=notes,
            display_order=display_order,
            created_by=user_id,
        )
        
        db.add(bom_entry)
        db.commit()
        db.refresh(bom_entry)
        
        # Log audit entry
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type="BILL_OF_MATERIAL",
            entity_id=bom_entry.id,
            entity_name=f"{parent_item.name} -> {component_item.name}",
            changes={
                "parent_item": parent_item.name,
                "component_item": component_item.name,
                "quantity_required": quantity_required,
            },
            request=request,
        )
        
        return bom_entry

    def update_bom_entry(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        bom_id: UUID,
        quantity_required: Optional[int] = None,
        unit_of_measure: Optional[str] = None,
        notes: Optional[str] = None,
        display_order: Optional[int] = None,
        request: Optional[Request] = None,
    ) -> BillOfMaterial:
        """Update an existing BOM entry."""
        bom_entry = db.query(BillOfMaterial).filter(
            BillOfMaterial.id == bom_id
        ).first()
        
        if not bom_entry:
            raise ValueError("BOM entry not found")
        
        changes = {}
        
        if quantity_required is not None:
            changes["quantity_required"] = {
                "old": bom_entry.quantity_required,
                "new": quantity_required,
            }
            bom_entry.quantity_required = quantity_required
        
        if unit_of_measure is not None:
            changes["unit_of_measure"] = {
                "old": bom_entry.unit_of_measure,
                "new": unit_of_measure,
            }
            bom_entry.unit_of_measure = unit_of_measure
        
        if notes is not None:
            changes["notes"] = {"old": bom_entry.notes, "new": notes}
            bom_entry.notes = notes
        
        if display_order is not None:
            changes["display_order"] = {
                "old": bom_entry.display_order,
                "new": display_order,
            }
            bom_entry.display_order = display_order
        
        bom_entry.updated_by = user_id
        
        db.commit()
        db.refresh(bom_entry)
        
        if changes:
            audit_service.log(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                entity_type="BILL_OF_MATERIAL",
                entity_id=bom_entry.id,
                changes=changes,
                request=request,
            )
        
        return bom_entry

    def delete_bom_entry(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        bom_id: UUID,
        request: Optional[Request] = None,
    ) -> None:
        """Delete a BOM entry."""
        bom_entry = (
            db.query(BillOfMaterial)
            .filter(BillOfMaterial.id == bom_id)
            .options(
                joinedload(BillOfMaterial.parent_item),
                joinedload(BillOfMaterial.component_item),
            )
            .first()
        )
        
        if not bom_entry:
            raise ValueError("BOM entry not found")
        
        parent_name = bom_entry.parent_item.name if bom_entry.parent_item else "Unknown"
        component_name = bom_entry.component_item.name if bom_entry.component_item else "Unknown"
        
        db.delete(bom_entry)
        db.commit()
        
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type="BILL_OF_MATERIAL",
            entity_id=bom_id,
            entity_name=f"{parent_name} -> {component_name}",
            request=request,
        )

    def calculate_availability(
        self,
        db: Session,
        parent_item_id: UUID,
    ) -> dict:
        """
        Calculate how many assemblies can be built with current stock.
        
        Returns detailed availability for each component and the
        maximum number of assemblies that can be built.
        """
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == parent_item_id
        ).first()
        
        if not parent_item:
            raise ValueError("Parent item not found")
        
        bom_entries = self.get_bom_components(db, parent_item_id)
        
        if not bom_entries:
            return {
                "parent_item_id": str(parent_item_id),
                "parent_item_name": parent_item.name,
                "max_buildable": 0,
                "components": [],
                "message": "No components defined in BOM",
            }
        
        components_availability = []
        min_buildable = float("inf")
        limiting_component = None
        
        for entry in bom_entries:
            component = entry.component_item
            available_qty = component.quantity if component else 0
            qty_required = entry.quantity_required
            
            max_from_component = available_qty // qty_required if qty_required > 0 else 0
            
            component_info = {
                "component_item_id": str(entry.component_item_id),
                "component_name": component.name if component else "Unknown",
                "component_sku": component.sku if component else "Unknown",
                "quantity_required": qty_required,
                "quantity_available": available_qty,
                "max_assemblies": max_from_component,
                "is_limiting": False,
            }
            
            if max_from_component < min_buildable:
                min_buildable = max_from_component
                limiting_component = component_info
            
            components_availability.append(component_info)
        
        # Mark the limiting component
        if limiting_component:
            limiting_component["is_limiting"] = True
        
        max_buildable = int(min_buildable) if min_buildable != float("inf") else 0
        
        return {
            "parent_item_id": str(parent_item_id),
            "parent_item_name": parent_item.name,
            "max_buildable": max_buildable,
            "components": components_availability,
        }

    def build_assembly(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        parent_item_id: UUID,
        quantity_to_build: int,
        notes: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> dict:
        """
        Build assemblies from components.
        
        This will:
        - Decrease component quantities
        - Increase parent item quantity
        - Create stock movements for audit trail
        """
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == parent_item_id
        ).first()
        
        if not parent_item:
            raise ValueError("Parent item not found")
        
        bom_entries = self.get_bom_components(db, parent_item_id)
        
        if not bom_entries:
            raise ValueError("No BOM defined for this item")
        
        # Check availability
        availability = self.calculate_availability(db, parent_item_id)
        if quantity_to_build > availability["max_buildable"]:
            raise ValueError(
                f"Insufficient components. Maximum buildable: {availability['max_buildable']}"
            )
        
        components_consumed = []
        
        # Consume components
        for entry in bom_entries:
            component = entry.component_item
            qty_to_consume = entry.quantity_required * quantity_to_build
            
            component.quantity -= qty_to_consume
            
            # Update component status
            self._update_item_status(component)
            
            # Create stock movement for component consumption
            movement = StockMovement(
                tenant_id=tenant_id,
                inventory_item_id=component.id,
                movement_type=MovementType.ADJUSTMENT,
                quantity_change=-qty_to_consume,
                quantity_before=component.quantity + qty_to_consume,
                quantity_after=component.quantity,
                reference_number=f"BUILD-{parent_item.sku}",
                notes=f"Used in assembly: {parent_item.name} x{quantity_to_build}",
                performed_by=user_id,
            )
            db.add(movement)
            
            components_consumed.append({
                "component_item_id": str(component.id),
                "component_name": component.name,
                "quantity_consumed": qty_to_consume,
                "new_quantity": component.quantity,
            })
        
        # Increase parent item quantity
        old_parent_qty = parent_item.quantity
        parent_item.quantity += quantity_to_build
        self._update_item_status(parent_item)
        
        # Create stock movement for assembly
        assembly_movement = StockMovement(
            tenant_id=tenant_id,
            inventory_item_id=parent_item.id,
            movement_type=MovementType.ADJUSTMENT,
            quantity_change=quantity_to_build,
            quantity_before=old_parent_qty,
            quantity_after=parent_item.quantity,
            reference_number=f"BUILD-{parent_item.sku}",
            notes=notes or f"Assembled {quantity_to_build} units",
            performed_by=user_id,
        )
        db.add(assembly_movement)
        
        db.commit()
        
        # Log audit entry
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="BOM_BUILD",
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=parent_item_id,
            entity_name=parent_item.name,
            changes={
                "quantity_built": quantity_to_build,
                "components_consumed": components_consumed,
            },
            request=request,
        )
        
        return {
            "success": True,
            "quantity_built": quantity_to_build,
            "parent_item_id": str(parent_item_id),
            "parent_item_name": parent_item.name,
            "new_parent_quantity": parent_item.quantity,
            "components_consumed": components_consumed,
            "message": f"Successfully built {quantity_to_build} {parent_item.name}",
        }

    def unbuild_assembly(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        parent_item_id: UUID,
        quantity_to_unbuild: int,
        notes: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> dict:
        """
        Disassemble items back into components.
        
        This will:
        - Decrease parent item quantity
        - Increase component quantities
        - Create stock movements for audit trail
        """
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == parent_item_id
        ).first()
        
        if not parent_item:
            raise ValueError("Parent item not found")
        
        if parent_item.quantity < quantity_to_unbuild:
            raise ValueError(
                f"Insufficient quantity. Available: {parent_item.quantity}"
            )
        
        bom_entries = self.get_bom_components(db, parent_item_id)
        
        if not bom_entries:
            raise ValueError("No BOM defined for this item")
        
        components_returned = []
        
        # Return components
        for entry in bom_entries:
            component = entry.component_item
            qty_to_return = entry.quantity_required * quantity_to_unbuild
            
            old_component_qty = component.quantity
            component.quantity += qty_to_return
            
            # Update component status
            self._update_item_status(component)
            
            # Create stock movement for component return
            movement = StockMovement(
                tenant_id=tenant_id,
                inventory_item_id=component.id,
                movement_type=MovementType.ADJUSTMENT,
                quantity_change=qty_to_return,
                quantity_before=old_component_qty,
                quantity_after=component.quantity,
                reference_number=f"UNBUILD-{parent_item.sku}",
                notes=f"Returned from disassembly: {parent_item.name} x{quantity_to_unbuild}",
                performed_by=user_id,
            )
            db.add(movement)
            
            components_returned.append({
                "component_item_id": str(component.id),
                "component_name": component.name,
                "quantity_returned": qty_to_return,
                "new_quantity": component.quantity,
            })
        
        # Decrease parent item quantity
        old_parent_qty = parent_item.quantity
        parent_item.quantity -= quantity_to_unbuild
        self._update_item_status(parent_item)
        
        # Create stock movement for disassembly
        disassembly_movement = StockMovement(
            tenant_id=tenant_id,
            inventory_item_id=parent_item.id,
            movement_type=MovementType.ADJUSTMENT,
            quantity_change=-quantity_to_unbuild,
            quantity_before=old_parent_qty,
            quantity_after=parent_item.quantity,
            reference_number=f"UNBUILD-{parent_item.sku}",
            notes=notes or f"Disassembled {quantity_to_unbuild} units",
            performed_by=user_id,
        )
        db.add(disassembly_movement)
        
        db.commit()
        
        # Log audit entry
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="BOM_UNBUILD",
            entity_type=EntityType.INVENTORY_ITEM,
            entity_id=parent_item_id,
            entity_name=parent_item.name,
            changes={
                "quantity_unbuilt": quantity_to_unbuild,
                "components_returned": components_returned,
            },
            request=request,
        )
        
        return {
            "success": True,
            "quantity_unbuilt": quantity_to_unbuild,
            "parent_item_id": str(parent_item_id),
            "parent_item_name": parent_item.name,
            "new_parent_quantity": parent_item.quantity,
            "components_returned": components_returned,
            "message": f"Successfully disassembled {quantity_to_unbuild} {parent_item.name}",
        }

    def _would_create_cycle(
        self,
        db: Session,
        parent_item_id: UUID,
        new_component_id: UUID,
    ) -> bool:
        """
        Check if adding a component would create a circular reference.
        
        A cycle exists if the new component already uses the parent
        (directly or indirectly) in its own BOM.
        """
        visited = set()
        
        def has_path_to_parent(current_id: UUID) -> bool:
            if current_id == parent_item_id:
                return True
            if current_id in visited:
                return False
            
            visited.add(current_id)
            
            # Get all components of current item
            components = db.query(BillOfMaterial).filter(
                BillOfMaterial.parent_item_id == current_id
            ).all()
            
            for comp in components:
                if has_path_to_parent(comp.component_item_id):
                    return True
            
            return False
        
        return has_path_to_parent(new_component_id)

    def _update_item_status(self, item: InventoryItem) -> None:
        """Update item status based on quantity and reorder point."""
        if item.quantity <= 0:
            item.status = "out_of_stock"
        elif item.quantity <= item.reorder_point:
            item.status = "low_stock"
        else:
            item.status = "in_stock"


# Singleton instance
bom_service = BOMService()
