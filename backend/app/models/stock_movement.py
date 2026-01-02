import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base


class MovementType(str, enum.Enum):
    RECEIVE = "receive"
    SHIP = "ship"
    TRANSFER = "transfer"
    ADJUST = "adjust"
    COUNT = "count"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id"),
        nullable=False,
        index=True,
    )
    movement_type = Column(
        Enum(MovementType, name="movement_type_enum"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)  # Positive for in, negative for out
    from_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )
    to_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )
    reference_number = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    inventory_item = relationship("InventoryItem", backref="stock_movements")
    from_location = relationship(
        "Location", foreign_keys=[from_location_id], backref="outbound_movements"
    )
    to_location = relationship(
        "Location", foreign_keys=[to_location_id], backref="inbound_movements"
    )
