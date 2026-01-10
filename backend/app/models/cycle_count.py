"""
Cycle count models to support scheduled physical inventory counts,
line-item variances, and downstream adjustments.
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CycleCountStatus(str, Enum):
    """Lifecycle status for a cycle count."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    CANCELLED = "cancelled"


class CycleCount(Base):
    """Represents a scheduled physical inventory count."""

    __tablename__ = "cycle_counts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scheduled_date = Column(Date, nullable=False)
    status = Column(
        SQLEnum(
            CycleCountStatus,
            name="cycle_count_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=CycleCountStatus.SCHEDULED,
        index=True,
    )

    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    tenant = relationship("Tenant", backref="cycle_counts")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    line_items = relationship(
        "CycleCountLineItem",
        back_populates="cycle_count",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CycleCount {self.id} {self.status.value} on {self.scheduled_date}>"


class CycleCountLineItem(Base):
    """Line items for a cycle count, recording expected vs counted quantities."""

    __tablename__ = "cycle_count_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cycle_count_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cycle_counts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location_id = Column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    expected_quantity = Column(Integer, nullable=False, default=0)
    counted_quantity = Column(Integer, nullable=False, default=0)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    tenant = relationship("Tenant")
    cycle_count = relationship("CycleCount", back_populates="line_items")
    item = relationship("InventoryItem", backref="cycle_count_line_items")
    location = relationship("Location", backref="cycle_count_line_items")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<CycleCountLineItem item={self.item_id} expected={self.expected_quantity} counted={self.counted_quantity}>"

    @property
    def variance(self) -> int:
        """Computed variance: counted minus expected."""
        return int(self.counted_quantity) - int(self.expected_quantity)

    __table_args__ = (
        Index(
            "ix_cycle_count_line_items_tenant_cycle_item",
            "tenant_id",
            "cycle_count_id",
            "item_id",
        ),
    )
