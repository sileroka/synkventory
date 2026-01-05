"""
Revision service for managing inventory item version history.

Usage:
    from app.services.revision import revision_service

    # Create initial revision when item is created:
    revision_service.create_revision(
        db=db,
        tenant_id=tenant.id,
        item=item,
        user_id=user.id,
        revision_type=RevisionType.CREATE,
    )

    # Create revision when item is updated:
    revision_service.create_update_revision(
        db=db,
        tenant_id=tenant.id,
        item=item,
        old_values=old_values,
        user_id=user.id,
    )
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.item_revision import ItemRevision, RevisionType
from app.models.inventory import InventoryItem

logger = logging.getLogger(__name__)


class RevisionService:
    """Service for managing item revisions."""

    # Fields to track for changes
    TRACKED_FIELDS = [
        "name",
        "sku",
        "description",
        "quantity",
        "reorder_point",
        "unit_price",
        "status",
        "category_id",
        "location_id",
        "image_key",
        "custom_attributes",
    ]

    def _get_next_revision_number(
        self, db: Session, inventory_item_id: UUID
    ) -> int:
        """Get the next revision number for an item."""
        max_revision = (
            db.query(func.max(ItemRevision.revision_number))
            .filter(ItemRevision.inventory_item_id == inventory_item_id)
            .scalar()
        )
        return (max_revision or 0) + 1

    def _build_item_snapshot(self, item: InventoryItem) -> Dict[str, Any]:
        """Build a snapshot dictionary from an inventory item."""
        return {
            "name": item.name,
            "sku": item.sku,
            "description": item.description,
            "quantity": item.quantity,
            "reorder_point": item.reorder_point,
            "unit_price": item.unit_price,
            "status": item.status,
            "category_id": item.category_id,
            "location_id": item.location_id,
            "image_key": item.image_key,
            "custom_attributes": item.custom_attributes,
        }

    def _compute_changes(
        self, old_values: Dict[str, Any], new_values: Dict[str, Any]
    ) -> tuple:
        """
        Compute the changes between old and new values.

        Returns:
            Tuple of (changes_dict, change_summary)
        """
        changes = {}
        changed_fields = []

        for field in self.TRACKED_FIELDS:
            old_val = old_values.get(field)
            new_val = new_values.get(field)

            # Convert UUIDs to strings for comparison
            if hasattr(old_val, "hex"):
                old_val = str(old_val)
            if hasattr(new_val, "hex"):
                new_val = str(new_val)

            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
                changed_fields.append(field)

        # Build human-readable summary
        if changed_fields:
            if len(changed_fields) == 1:
                change_summary = f"Updated {changed_fields[0]}"
            elif len(changed_fields) <= 3:
                change_summary = f"Updated {', '.join(changed_fields)}"
            else:
                change_summary = f"Updated {len(changed_fields)} fields"
        else:
            change_summary = "No changes"

        return changes, change_summary

    def create_revision(
        self,
        db: Session,
        tenant_id: UUID,
        item: InventoryItem,
        user_id: Optional[UUID],
        revision_type: str = RevisionType.CREATE,
        old_values: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None,
    ) -> Optional[ItemRevision]:
        """
        Create a new revision for an inventory item.

        Args:
            db: Database session
            tenant_id: Tenant ID
            item: The inventory item
            user_id: User ID who made the change
            revision_type: Type of revision (CREATE, UPDATE, RESTORE)
            old_values: Previous values (for UPDATE type)
            change_summary: Optional custom change summary

        Returns:
            Created ItemRevision or None if failed
        """
        try:
            revision_number = self._get_next_revision_number(db, item.id)
            item_snapshot = self._build_item_snapshot(item)

            changes = None
            summary = change_summary

            if revision_type == RevisionType.CREATE:
                summary = summary or "Item created"
            elif revision_type == RevisionType.RESTORE:
                summary = summary or "Restored from previous revision"
            elif old_values:
                changes, computed_summary = self._compute_changes(
                    old_values, item_snapshot
                )
                summary = summary or computed_summary

            revision = ItemRevision(
                tenant_id=tenant_id,
                inventory_item_id=item.id,
                revision_number=revision_number,
                revision_type=revision_type,
                changes=changes,
                change_summary=summary,
                created_by=user_id,
                **item_snapshot,
            )

            db.add(revision)
            db.flush()  # Get ID without committing

            logger.info(
                f"Created revision {revision_number} for item {item.id} "
                f"(type: {revision_type})"
            )

            return revision

        except Exception as e:
            logger.error(f"Failed to create revision: {e}")
            return None

    def create_update_revision(
        self,
        db: Session,
        tenant_id: UUID,
        item: InventoryItem,
        old_values: Dict[str, Any],
        user_id: Optional[UUID],
    ) -> Optional[ItemRevision]:
        """
        Convenience method to create an UPDATE revision.

        Args:
            db: Database session
            tenant_id: Tenant ID
            item: The updated inventory item
            old_values: Values before the update
            user_id: User ID who made the change

        Returns:
            Created ItemRevision or None if failed
        """
        return self.create_revision(
            db=db,
            tenant_id=tenant_id,
            item=item,
            user_id=user_id,
            revision_type=RevisionType.UPDATE,
            old_values=old_values,
        )

    def get_revisions(
        self,
        db: Session,
        inventory_item_id: UUID,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """
        Get revisions for an inventory item.

        Returns:
            Tuple of (revisions, total_count)
        """
        query = (
            db.query(ItemRevision)
            .filter(ItemRevision.inventory_item_id == inventory_item_id)
            .order_by(ItemRevision.revision_number.desc())
        )

        total = query.count()
        skip = (page - 1) * page_size
        revisions = query.offset(skip).limit(page_size).all()

        return revisions, total

    def get_revision(
        self,
        db: Session,
        inventory_item_id: UUID,
        revision_number: int,
    ) -> Optional[ItemRevision]:
        """Get a specific revision by revision number."""
        return (
            db.query(ItemRevision)
            .filter(
                ItemRevision.inventory_item_id == inventory_item_id,
                ItemRevision.revision_number == revision_number,
            )
            .first()
        )

    def get_latest_revision(
        self, db: Session, inventory_item_id: UUID
    ) -> Optional[ItemRevision]:
        """Get the latest revision for an item."""
        return (
            db.query(ItemRevision)
            .filter(ItemRevision.inventory_item_id == inventory_item_id)
            .order_by(ItemRevision.revision_number.desc())
            .first()
        )

    def compare_revisions(
        self,
        db: Session,
        inventory_item_id: UUID,
        from_revision_number: int,
        to_revision_number: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two revisions and return the differences.

        Returns:
            Dict with from_revision, to_revision, and differences
        """
        from_rev = self.get_revision(db, inventory_item_id, from_revision_number)
        to_rev = self.get_revision(db, inventory_item_id, to_revision_number)

        if not from_rev or not to_rev:
            return None

        from_snapshot = self._build_item_snapshot_from_revision(from_rev)
        to_snapshot = self._build_item_snapshot_from_revision(to_rev)

        differences, _ = self._compute_changes(from_snapshot, to_snapshot)

        return {
            "from_revision": from_rev,
            "to_revision": to_rev,
            "differences": differences,
        }

    def _build_item_snapshot_from_revision(
        self, revision: ItemRevision
    ) -> Dict[str, Any]:
        """Build a snapshot dictionary from a revision."""
        return {
            "name": revision.name,
            "sku": revision.sku,
            "description": revision.description,
            "quantity": revision.quantity,
            "reorder_point": revision.reorder_point,
            "unit_price": revision.unit_price,
            "status": revision.status,
            "category_id": str(revision.category_id) if revision.category_id else None,
            "location_id": str(revision.location_id) if revision.location_id else None,
            "image_key": revision.image_key,
            "custom_attributes": revision.custom_attributes,
        }

    def restore_revision(
        self,
        db: Session,
        tenant_id: UUID,
        item: InventoryItem,
        revision: ItemRevision,
        user_id: Optional[UUID],
        reason: Optional[str] = None,
    ) -> ItemRevision:
        """
        Restore an inventory item to a previous revision state.

        Args:
            db: Database session
            tenant_id: Tenant ID
            item: Current inventory item
            revision: The revision to restore to
            user_id: User ID performing the restore
            reason: Optional reason for the restore

        Returns:
            The new revision created after restore
        """
        # Capture current state
        old_values = self._build_item_snapshot(item)

        # Apply the revision's values to the item
        item.name = revision.name
        item.sku = revision.sku
        item.description = revision.description
        item.quantity = revision.quantity
        item.reorder_point = revision.reorder_point
        item.unit_price = revision.unit_price
        item.status = revision.status
        item.category_id = revision.category_id
        item.location_id = revision.location_id
        item.image_key = revision.image_key
        item.custom_attributes = revision.custom_attributes
        item.updated_by = user_id

        db.flush()

        # Create a new RESTORE revision
        summary = f"Restored to revision {revision.revision_number}"
        if reason:
            summary += f": {reason}"

        return self.create_revision(
            db=db,
            tenant_id=tenant_id,
            item=item,
            user_id=user_id,
            revision_type=RevisionType.RESTORE,
            old_values=old_values,
            change_summary=summary,
        )


# Singleton instance
revision_service = RevisionService()
