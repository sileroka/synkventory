import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class InventoryLocationQuantity(Base):
    """
    Tracks inventory quantity per location.
    The inventory_items.quantity is the total across all locations.
    """

    __tablename__ = "inventory_location_quantities"

    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, default=0, nullable=False)
    bin_location = Column(String(100), nullable=True)  # Shelf/bin identifier
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite primary key
    __table_args__ = (PrimaryKeyConstraint("inventory_item_id", "location_id"),)

    # Relationships
    inventory_item = relationship(
        "InventoryItem", backref="location_quantities", lazy="joined"
    )
    location = relationship("Location", backref="inventory_quantities", lazy="joined")
