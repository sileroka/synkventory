import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String, index=True, nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    category = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
