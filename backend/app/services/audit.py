"""
Audit logging service for tracking all system activities.

Usage:
    from app.services.audit import audit_service

    # In an endpoint with request and user context:
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        user_id=user.id,
        action=AuditAction.CREATE,
        entity_type=EntityType.INVENTORY_ITEM,
        entity_id=item.id,
        entity_name=item.name,
        changes={"sku": item.sku, "quantity": item.quantity},
        request=request,
    )
"""

import logging
from typing import Optional, Dict, Any
import uuid
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction, EntityType
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating audit log entries."""

    def _get_request_context(self, request: Optional[Request]) -> tuple:
        """Extract IP address and user agent from request."""
        ip_address = None
        user_agent = None

        if request:
            # Get real IP from X-Forwarded-For or client host
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                ip_address = forwarded_for.split(",")[0].strip()
            elif request.client:
                ip_address = request.client.host

            user_agent = request.headers.get("user-agent", "")[:512]

        return ip_address, user_agent

    def _get_user_email(self, db: Session, user_id: Optional[UUID]) -> Optional[str]:
        """Get user email from user_id."""
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        return user.email if user else None

    def log(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: Optional[UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        entity_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """
        Create an audit log entry.

        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID who performed the action
            action: Action type (use AuditAction constants)
            entity_type: Entity type (use EntityType constants)
            entity_id: ID of the affected entity
            entity_name: Human-readable name of the entity
            changes: Dict of changes made (for updates: {field: {old, new}})
            extra_data: Additional context data
            request: FastAPI request object (for IP, user agent)

        Returns:
            Created AuditLog entry or None if failed
        """
        try:
            ip_address, user_agent = self._get_request_context(request)

            # Get user email directly from user_id query to avoid session issues
            user_email = None
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                user_email = user.email if user else None

            # Create audit log entry
            # Cast UUIDs to strings for cross-dialect compatibility (e.g., SQLite tests)
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                tenant_id=str(tenant_id) if tenant_id is not None else None,
                user_id=str(user_id) if user_id is not None else None,
                user_email=user_email,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                entity_name=entity_name,
                changes=changes,
                extra_data=extra_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(audit_log)
            # Use flush instead of commit to add to transaction without committing
            # The calling code will commit the overall transaction
            db.flush()

            logger.debug(
                f"Audit log created: {action} {entity_type} "
                f"by {user_email or 'system'}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't rollback - audit logging failure should not affect the main transaction
            # The calling code has already captured necessary data before calling audit
            return None

    def log_login(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log a successful login."""
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LOGIN,
            entity_type=EntityType.USER,
            entity_id=user_id,
            request=request,
        )

    def log_logout(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log a logout event."""
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LOGOUT,
            entity_type=EntityType.USER,
            entity_id=user_id,
            request=request,
        )

    def log_create(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log an entity creation."""
        # Serialize UUIDs in data
        if data:
            data = self._serialize_data(data)

        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=data,
            request=request,
        )

    def log_update(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log an entity update with changes dict."""
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            request=request,
        )

    def log_delete(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log an entity deletion."""
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=data,
            request=request,
        )

    def log_stock_movement(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        movement_type: str,
        item_id: UUID,
        item_name: str,
        quantity_change: int,
        old_quantity: int,
        new_quantity: int,
        from_location_id: Optional[UUID] = None,
        to_location_id: Optional[UUID] = None,
        reference_number: Optional[str] = None,
        reason: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log a stock movement with details."""
        changes = {
            "quantity_change": quantity_change,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
        }
        if from_location_id:
            changes["from_location_id"] = str(from_location_id)
        if to_location_id:
            changes["to_location_id"] = str(to_location_id)
        if reference_number:
            changes["reference_number"] = reference_number
        if reason:
            changes["reason"] = reason

        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=movement_type,
            entity_type=EntityType.STOCK_MOVEMENT,
            entity_id=item_id,
            entity_name=item_name,
            changes=changes,
            request=request,
        )

    def log_bulk_operation(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        action: str,
        entity_type: str,
        count: int,
        data: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Optional[AuditLog]:
        """Log a bulk operation."""
        extra_data = {
            "count": count,
        }
        if data:
            extra_data.update(data)

        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            extra_data=extra_data,
            request=request,
        )

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize UUIDs and other non-JSON types in data dict."""
        result = {}
        for key, value in data.items():
            if hasattr(value, "hex"):  # UUID
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._serialize_data(value)
            elif isinstance(value, list):
                result[key] = [str(v) if hasattr(v, "hex") else v for v in value]
            else:
                result[key] = value
        return result


# Singleton instance
audit_service = AuditService()
