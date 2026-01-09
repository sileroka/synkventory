"""
ItemConsumption model for recording historical consumption (outflows).
"""

import uuid
from datetime import datetime, date
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ConsumptionSource(str, Enum):
    SALES_ORDER = "sales_order"
    WORK_ORDER = "work_order"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    OTHER = "other"


class ItemConsumption(Base):
    __tablename__ = "item_consumption"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The calendar date of consumption (UTC)
    date = Column(Date, nullable=False)

    # Quantity consumed (positive number for outflows)
    quantity = Column(Numeric(12, 2), nullable=False)

    # Source of the consumption (sales orders, work orders, adjustments, etc.)
    source = Column(
        SQLEnum(
            ConsumptionSource,
            name="consumption_source",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ConsumptionSource.OTHER,
        index=True,
    )

    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant")
    item = relationship("InventoryItem", backref="consumption_records")

    def __repr__(self) -> str:
        return f"<ItemConsumption item={self.item_id} date={self.date} qty={self.quantity} source={self.source}>"
