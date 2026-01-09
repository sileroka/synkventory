"""
Service layer for Customer management.

Provides CRUD helpers with audit logging and tenant scoping.
"""

import logging
import uuid
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.models.audit_log import AuditAction, EntityType
from app.models.customer import Customer
from app.services.audit import audit_service

logger = logging.getLogger(__name__)


class CustomerService:
    """Customer service with CRUD operations and audit logging."""

    def get_customers(
        self,
        db: Session,
        tenant_id: UUID,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Tuple[List[Customer], int]:
        """Return paginated customers with optional name/email search."""
        page = max(page, 1)
        page_size = max(page_size, 1)

        query = db.query(Customer).filter(Customer.tenant_id == tenant_id)

        if search:
            like = f"%{search}%"
            query = query.filter(
                (Customer.name.ilike(like)) | (Customer.email.ilike(like))
            )

        total = query.count()
        customers = (
            query.order_by(Customer.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return customers, total

    def create_customer(
        self,
        db: Session,
        user_id: Optional[UUID],
        **data,
    ) -> Customer:
        """Create a customer and record an audit log."""
        tenant = get_current_tenant()
        customer = Customer(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            created_by=user_id,
            updated_by=user_id,
            **data,
        )
        db.add(customer)
        db.flush()

        audit_service.log(
            db=db,
            tenant_id=tenant.id,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type=EntityType.CUSTOMER,
            entity_id=str(customer.id),
            entity_name=customer.name,
            changes=data,
        )

        logger.debug("Created customer %s", customer.id)
        return customer

    def get_customer(
        self, db: Session, tenant_id: UUID, customer_id: UUID
    ) -> Optional[Customer]:
        """Fetch a single customer scoped to tenant."""
        return (
            db.query(Customer)
            .filter(
                Customer.id == str(customer_id),
                Customer.tenant_id == str(tenant_id),
            )
            .first()
        )

    def update_customer(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        customer_id: UUID,
        **changes,
    ) -> Optional[Customer]:
        """Update customer fields and audit the change."""
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return None

        change_log = {}
        for field, value in changes.items():
            if hasattr(customer, field):
                old = getattr(customer, field)
                if old != value:
                    setattr(customer, field, value)
                    change_log[field] = {"old": old, "new": value}

        if change_log:
            customer.updated_by = user_id
            audit_service.log(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                entity_type=EntityType.CUSTOMER,
                entity_id=customer.id,
                entity_name=customer.name,
                changes=change_log,
            )
            logger.debug("Updated customer %s", customer.id)

        return customer

    def delete_customer(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        customer_id: UUID,
    ) -> bool:
        """Deactivate customer; hard delete if no sales orders reference it (future)."""
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return False

        # For now, always soft-delete to preserve history
        if customer.is_active:
            customer.is_active = False
            customer.updated_by = user_id
            audit_service.log(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                entity_type=EntityType.CUSTOMER,
                entity_id=customer.id,
                entity_name=customer.name,
                changes={"is_active": {"old": True, "new": False}},
            )

        logger.debug("Deactivated customer %s", customer.id)
        return True


customer_service = CustomerService()