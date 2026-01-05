"""
ItemRevision model for tracking version history of inventory items.

This implements revision control functionality, storing a snapshot of
inventory item data each time a change is made.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ItemRevision(Base):
    """
    Stores historical versions of inventory items.

    Each time an inventory item is created or modified, a new revision
    is created capturing the complete state at that point in time.
    This allows for:
    - Full audit trail of changes
    - Ability to view item state at any point in history
    - Comparison between revisions
    - Potential rollback to previous states
    """

    __tablename__ = "item_revisions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reference to the inventory item
    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Revision metadata
    revision_number = Column(Integer, nullable=False)
    revision_type = Column(
        String(50), nullable=False, index=True
    )  # CREATE, UPDATE, RESTORE

    # Snapshot of inventory item fields at this revision
    name = Column(String(255), nullable=False)
    sku = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    category_id = Column(UUID(as_uuid=True), nullable=True)
    location_id = Column(UUID(as_uuid=True), nullable=True)
    image_key = Column(String(512), nullable=True)
    custom_attributes = Column(JSONB, nullable=True)

    # Change details - what changed from the previous revision
    changes = Column(JSONB, nullable=True)  # {field: {old: x, new: y}}
    change_summary = Column(String(500), nullable=True)  # Human-readable summary

    # Who made the change
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # When the revision was created
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index(
            "ix_item_revisions_item_revision",
            "inventory_item_id",
            "revision_number",
            unique=True,
        ),
        Index("ix_item_revisions_tenant_item", "tenant_id", "inventory_item_id"),
        Index("ix_item_revisions_tenant_created", "tenant_id", "created_at"),
    )

    # Relationships
    tenant = relationship("Tenant", backref="item_revisions")
    inventory_item = relationship("InventoryItem", backref="revisions")
    creator = relationship("User", foreign_keys=[created_by], backref="item_revisions")

    def __repr__(self) -> str:
        return f"<ItemRevision {self.inventory_item_id} v{self.revision_number}>"


class RevisionType:
    """Standard revision types."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    RESTORE = "RESTORE"  # When restoring from a previous revision
