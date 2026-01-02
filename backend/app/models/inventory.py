import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
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
    name = Column(String(255), index=True, nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=False)
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
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    category = relationship("Category", backref="inventory_items")
    location = relationship("Location", backref="inventory_items")
