"""
Service layer for Supplier management.

Provides CRUD helpers with audit logging and tenant scoping.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder
from app.models.audit_log import AuditAction, EntityType
from app.services.audit import audit_service

logger = logging.getLogger(__name__)


class SupplierService:
    """Supplier service with CRUD operations and audit logging."""

    def get_suppliers(
        self,
        db: Session,
        tenant_id: UUID,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Tuple[List[Supplier], int]:
        """Return paginated suppliers with optional name search."""
        page = max(page, 1)
        page_size = max(page_size, 1)

        query = db.query(Supplier).filter(Supplier.tenant_id == tenant_id)

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(Supplier.name.ilike(like_pattern))

        total = query.count()
        suppliers = (
            query.order_by(Supplier.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return suppliers, total

    def create_supplier(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        **supplier_data,
    ) -> Supplier:
        """Create a supplier and record an audit log."""
        supplier = Supplier(
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **supplier_data,
        )
        db.add(supplier)
        db.flush()

        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type=EntityType.SUPPLIER,
            entity_id=supplier.id,
            entity_name=supplier.name,
            changes=supplier_data,
        )

        logger.debug("Created supplier %s", supplier.id)
        return supplier

    def get_supplier(
        self, db: Session, tenant_id: UUID, supplier_id: UUID
    ) -> Optional[Supplier]:
        """Fetch a single supplier scoped to tenant."""
        return (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id)
            .first()
        )

    def update_supplier(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        supplier_id: UUID,
        **changes,
    ) -> Optional[Supplier]:
        """Update supplier fields and audit the change."""
        supplier = self.get_supplier(db, tenant_id, supplier_id)
        if not supplier:
            return None

        # Track old vs new for audit
        change_log = {}
        for field, value in changes.items():
            if hasattr(supplier, field):
                old = getattr(supplier, field)
                if old != value:
                    setattr(supplier, field, value)
                    change_log[field] = {"old": old, "new": value}

        if change_log:
            supplier.updated_by = user_id
            audit_service.log(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                entity_type=EntityType.SUPPLIER,
                entity_id=supplier.id,
                entity_name=supplier.name,
                changes=change_log,
            )
            logger.debug("Updated supplier %s", supplier.id)

        return supplier

    def delete_supplier(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        supplier_id: UUID,
    ) -> bool:
        """Soft-delete (deactivate) unless unused; delete if no POs reference it."""
        supplier = self.get_supplier(db, tenant_id, supplier_id)
        if not supplier:
            return False

        # Check purchase order references
        po_count = (
            db.query(func.count(PurchaseOrder.id))
            .filter(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.tenant_id == tenant_id,
            )
            .scalar()
        )

        if po_count and po_count > 0:
            # Soft delete: mark inactive
            if supplier.is_active:
                supplier.is_active = False
                supplier.updated_by = user_id
                audit_service.log(
                    db=db,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=AuditAction.UPDATE,
                    entity_type=EntityType.SUPPLIER,
                    entity_id=supplier.id,
                    entity_name=supplier.name,
                    changes={"is_active": {"old": True, "new": False}},
                )
            return False

        # Hard delete if no references
        db.delete(supplier)
        audit_service.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type=EntityType.SUPPLIER,
            entity_id=supplier.id,
            entity_name=supplier.name,
        )
        logger.debug("Deleted supplier %s", supplier.id)
        return True


supplier_service = SupplierService()
*** End Patch