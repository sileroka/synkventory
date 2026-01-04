import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), index=True, nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    reorder_point = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    status = Column(
        String(50),
        default="in_stock",
        nullable=False,
        index=True,
    )
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )
    location_id = Column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Image storage - stores the S3/Spaces object key (not full URL)
    image_key = Column(String(512), nullable=True)

    # Custom attributes - stores key-value pairs defined by category attributes
    custom_attributes = Column(JSONB, nullable=True, default=dict)

    # Indexes for multi-tenancy queries
    __table_args__ = (
        Index("ix_inventory_items_tenant_sku", "tenant_id", "sku", unique=True),
        Index("ix_inventory_items_tenant_status", "tenant_id", "status"),
        Index("ix_inventory_items_tenant_category", "tenant_id", "category_id"),
        Index("ix_inventory_items_tenant_location", "tenant_id", "location_id"),
    )

    # Relationships
    tenant = relationship("Tenant", backref="inventory_items")
    category = relationship("Category", backref="inventory_items")
    location = relationship("Location", backref="inventory_items")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_inventory_items"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], backref="updated_inventory_items"
    )
