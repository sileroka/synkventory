import uuid
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ItemLot(Base):
    __tablename__ = "item_lots"

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
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id"),
        nullable=False,
        index=True,
    )
    lot_number = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    expiration_date = Column(Date, nullable=True)
    manufacture_date = Column(Date, nullable=True)
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Indexes for multi-tenancy queries
    __table_args__ = (
        Index("ix_item_lots_tenant_item", "tenant_id", "item_id"),
        Index("ix_item_lots_tenant_lot_number", "tenant_id", "lot_number", unique=True),
        Index("ix_item_lots_tenant_location", "tenant_id", "location_id"),
        Index("ix_item_lots_expiration_date", "expiration_date"),
    )

    # Relationships
    tenant = relationship("Tenant", backref="item_lots")
    item = relationship("InventoryItem", back_populates="lots")
    location = relationship("Location", backref="item_lots")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_item_lots"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], backref="updated_item_lots"
    )
