"""
Work Order model for tracking production of assemblies.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class WorkOrderStatus(str, Enum):
    """Status values for work orders."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderPriority(str, Enum):
    """Priority levels for work orders."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WorkOrder(Base):
    """
    Work Order model for tracking production builds of assemblies.
    
    A work order represents a request to produce a certain quantity of
    an assembly item using its Bill of Materials.
    """
    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Work order identification
    work_order_number = Column(String(50), nullable=False, index=True)
    
    # The assembly item to build
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Quantities
    quantity_ordered = Column(Integer, nullable=False, default=1)
    quantity_completed = Column(Integer, nullable=False, default=0)
    quantity_scrapped = Column(Integer, nullable=False, default=0)
    
    # Status and priority
    status = Column(
        SQLEnum(WorkOrderStatus, name="work_order_status"),
        nullable=False,
        default=WorkOrderStatus.DRAFT,
        index=True,
    )
    priority = Column(
        SQLEnum(WorkOrderPriority, name="work_order_priority"),
        nullable=False,
        default=WorkOrderPriority.NORMAL,
    )
    
    # Dates
    due_date = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Optional location for output
    output_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Assigned user
    assigned_to_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Notes and description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Estimated cost (calculated from BOM)
    estimated_cost = Column(Numeric(12, 2), nullable=True)
    actual_cost = Column(Numeric(12, 2), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", backref="work_orders")
    item = relationship("InventoryItem", backref="work_orders", foreign_keys=[item_id])
    output_location = relationship("Location", backref="work_orders")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_work_orders")
    created_by_user = relationship("User", foreign_keys=[created_by], backref="created_work_orders")
    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<WorkOrder {self.work_order_number} - {self.status.value}>"

    @property
    def quantity_remaining(self) -> int:
        """Calculate remaining quantity to build."""
        return max(0, self.quantity_ordered - self.quantity_completed - self.quantity_scrapped)
    
    @property
    def is_overdue(self) -> bool:
        """Check if work order is overdue."""
        if not self.due_date or self.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.quantity_ordered == 0:
            return 0.0
        return (self.quantity_completed / self.quantity_ordered) * 100
